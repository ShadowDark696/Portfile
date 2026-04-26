# Sistema de Día/Noche (DayNightService)

> **Archivo principal:** `src/server/Services/DayNightService.luau`  
> **Tipo:** ModuleScript (servidor)  
> **RemoteEvent:** `ReplicatedStorage/Events/DayNight`  
> **Interacción directa con:** `MutationService` (reacciona a cambios de `Lighting.ClockTime`)

---

## 1. ¿Qué hace el sistema?

El `DayNightService` controla el **ciclo de día y noche** del juego Roblox. Gestiona:

1. Los **ajustes de iluminación** (`Lighting`) en cada fase del día
2. La **transición suavizada** entre fases usando `TweenService`
3. El **cambio de cielo** (Sky) entre día y noche
4. La **notificación a los clientes** mediante `RemoteEvent` para que puedan reaccionar (mostrar HUD de noche, cambiar música, etc.)

---

## 2. Las 3 Fases del Ciclo

El ciclo sigue siempre este orden y se repite infinitamente:

```
DÍA  (360s) → TARDE (120s) → NOCHE (300s) → DÍA (360s) → ...
```

### Duración total de un ciclo completo

```
360 + 120 + 300 = 780 segundos = 13 minutos
```

### Constantes de duración

```lua
DAY_DURATION       = 360   -- 6 minutos de día
AFTERNOON_DURATION = 120   -- 2 minutos de tarde
NIGHT_DURATION     = 300   -- 5 minutos de noche
TRANSITION_RATIO   = 0.1   -- 10% del tiempo es transición de tween
```

---

## 3. Cálculo de la Transición

```lua
local function computeTransition(duration)
    return math.max(2, math.min(duration, math.floor(duration * TRANSITION_RATIO)))
end
```

| Fase | Duración | Transición calculada |
|---|---|---|
| Día | 360s | `max(2, min(360, floor(36))) = 36 segundos` |
| Tarde | 120s | `max(2, min(120, floor(12))) = 12 segundos` |
| Noche | 300s | `max(2, min(300, floor(30))) = 30 segundos` |

El `math.max(2, ...)` garantiza que siempre hay al menos **2 segundos de tween**, evitando cambios instantáneos bruscos.

---

## 4. Configuración de Iluminación por Fase

### Fase DÍA (`daySettings`)

| Propiedad | Valor |
|---|---|
| ClockTime | 14.5 (2:30 PM → sol alto) |
| Brightness | 2 |
| Ambient | RGB(241, 241, 241) → casi blanco |
| OutdoorAmbient | RGB(212, 212, 212) → gris claro |
| GeographicLatitude | 5° (zona ecuatorial → sol muy alto) |
| ColorShift_Top | RGB(150, 150, 232) → leve tinte azul-violeta arriba |
| ColorShift_Bottom | RGB(150, 150, 232) → igual abajo |
| FogColor | RGB(180, 200, 230) → niebla azul clara |
| FogEnd | 10000 → niebla muy lejana (casi invisible) |
| FogStart | 0 |
| SunIntensity | 1.2 → sol brillante |
| MoonIntensity | 0 → luna apagada |

### Fase TARDE (`afternoonSettings`)

| Propiedad | Valor |
|---|---|
| ClockTime | 17 (5:00 PM → sol bajo) |
| Brightness | 1.5 → algo más oscuro |
| Ambient | RGB(180, 140, 100) → naranja cálido |
| OutdoorAmbient | RGB(160, 120, 80) → más oscuro, tonos tierra |
| GeographicLatitude | 41.7° (latitud media → sol más inclinado) |
| ColorShift_Top | RGB(255, 150, 50) → naranja brillante arriba |
| ColorShift_Bottom | RGB(255, 200, 100) → amarillo cálido abajo |
| FogColor | RGB(255, 180, 120) → niebla anaranjada (atardecer) |
| FogEnd | 8000 → niebla más cercana que de día |
| FogStart | 0 |
| SunIntensity | 0.7 → sol tenue de atardecer |
| MoonIntensity | 0 |

### Fase NOCHE (`nightSettings`)

| Propiedad | Valor |
|---|---|
| ClockTime | 0 (medianoche) |
| Brightness | 2.5 → más brillante que el día para que se vea el mapa |
| Ambient | RGB(150, 150, 190) → azul-violeta suave |
| OutdoorAmbient | RGB(170, 160, 190) → violeta pálido |
| GeographicLatitude | 5° (equatorial, igual que día) |
| ColorShift_Top | RGB(110, 90, 180) → violeta oscuro arriba |
| ColorShift_Bottom | RGB(90, 70, 160) → violeta más oscuro abajo |
| FogColor | RGB(80, 80, 100) → niebla oscura azul-gris |
| FogEnd | 10000 → niebla lejana |
| FogStart | 0 |
| SunIntensity | 0 → sin sol |
| MoonIntensity | 1 → luna a máxima intensidad |

---

## 5. Sistema de Transición con TweenService

### `applySettings(settings, duration)`

```lua
local goals = {
    ClockTime = settings.ClockTime,
    Brightness = settings.Brightness,
    Ambient = settings.Ambient,
    OutdoorAmbient = settings.OutdoorAmbient,
    GeographicLatitude = settings.GeographicLatitude,
    ColorShift_Top = settings.ColorShift_Top,
    ColorShift_Bottom = settings.ColorShift_Bottom,
    FogColor = settings.FogColor,
    FogEnd = settings.FogEnd,
    FogStart = settings.FogStart,
}

local tweenInfo = TweenInfo.new(
    duration,           -- duración calculada (36s / 12s / 30s)
    Enum.EasingStyle.Quad,      -- suavizado cuadrático
    Enum.EasingDirection.InOut  -- entra y sale suave
)

local lightingTween = TweenService:Create(Lighting, tweenInfo, goals)
lightingTween:Play()
```

- **EasingStyle.Quad + InOut**: la transición empieza lento, acelera en el medio y frena al final → efecto natural de amanecer/atardecer.
- El tween anima **10 propiedades de Lighting simultáneamente**.
- `SunIntensity` y `MoonIntensity` **no** se tween (no están en `goals`) → cambian junto con el sky al instante.

---

## 6. Sistema de Cielos (Sky)

El juego tiene **dos skies** en `Lighting`:
- `DaySky` → usado durante el Día y la Tarde
- `NightSky` → usado durante la Noche

### `setActiveSky(skyName)`

```lua
local function setActiveSky(skyName)
    for _, child in ipairs(Lighting:GetChildren()) do
        if child:IsA("Sky") then
            if child.Name == skyName then
                child.Parent = Lighting   -- activa este sky
            else
                child.Parent = nil        -- desactiva (saca del Lighting) el otro
            end
        end
    end
end
```

> Para "desactivar" un Sky en Roblox, se mueve fuera de Lighting (`.Parent = nil`). El Sky activo siempre permanece dentro de `Lighting`.

### Sky de respaldo (`getOrCreateSky`)

Si no existe ningún Sky en Lighting, se crea uno por defecto:

```lua
local sky = Instance.new("Sky")
sky.Name = "Sky"
sky.SunAngularSize = 21    -- tamaño del sol en grados
sky.MoonAngularSize = 11   -- tamaño de la luna en grados
sky.SkyboxBk = "rbxassetid://7078296966"  -- mismo asset para las 6 caras del skybox
sky.SkyboxDn = "rbxassetid://7078296966"
sky.SkyboxFt = "rbxassetid://7078296966"
sky.SkyboxLf = "rbxassetid://7078296966"
sky.SkyboxRt = "rbxassetid://7078296966"
sky.SkyboxUp = "rbxassetid://7078296966"
sky.StarCount = 500000        -- estrellas de noche
sky.CelestialBodiesShown = true  -- muestra sol y luna
```

---

## 7. El Loop Principal

### `DayNightService:Start()`

```lua
function DayNightService:Start()
    if isRunning then return end
    isRunning = true

    -- Configura la iluminación global
    Lighting.GlobalShadows = true    -- sombras activadas
    Lighting.ShadowSoftness = 0.5    -- sombras suaves (valor medio)
    Lighting.EnvironmentDiffuseScale = 1   -- luz ambiental máxima
    Lighting.EnvironmentSpecularScale = 1  -- reflejos máximos

    -- Sincroniza jugadores que entran tarde
    Players.PlayerAdded:Connect(function(p)
        local t = Lighting.ClockTime
        local state
        if t >= 6 and t < 14 then
            state = "Day"
        elseif t >= 14 and t < 18 then
            state = "Afternoon"
        else
            state = "Night"
        end
        dayNightEvent:FireClient(p, state)
    end)

    -- Loop infinito del ciclo
    task.spawn(function()
        while isRunning do
            updateDay()
            task.wait(DAY_DURATION)       -- espera 360 segundos
            updateAfternoon()
            task.wait(AFTERNOON_DURATION) -- espera 120 segundos
            updateNight()
            task.wait(NIGHT_DURATION)     -- espera 300 segundos
        end
    end)
end
```

### `DayNightService:Stop()`

```lua
function DayNightService:Stop()
    isRunning = false
    -- El loop de task.spawn verifica isRunning y para solo
end
```

---

## 8. Funciones de actualización por fase

### `updateDay()`
```lua
setActiveSky("DaySky")
applySettings(daySettings, 36)       -- tween de 36 segundos
dayNightEvent:FireAllClients("Day")  -- notifica a TODOS los clientes
```

### `updateAfternoon()`
```lua
setActiveSky("DaySky")               -- misma sky que el día
applySettings(afternoonSettings, 12) -- tween de 12 segundos
dayNightEvent:FireAllClients("Afternoon")
```

### `updateNight()`
```lua
setActiveSky("NightSky")
applySettings(nightSettings, 30)     -- tween de 30 segundos
dayNightEvent:FireAllClients("Night")
```

---

## 9. RemoteEvent `DayNight`

### Creación automática

```lua
local eventsFolder = ReplicatedStorage:FindFirstChild("Events")
-- Si no existe, lo crea
local dayNightEvent = eventsFolder:FindFirstChild("DayNight")
-- Si no existe, crea el RemoteEvent
```

### Mensajes enviados a los clientes

| Evento | Momento | Mensaje |
|---|---|---|
| `FireAllClients("Day")` | Al inicio del período día | `"Day"` |
| `FireAllClients("Afternoon")` | Al inicio del período tarde | `"Afternoon"` |
| `FireAllClients("Night")` | Al inicio del período noche | `"Night"` |
| `FireClient(p, state)` | Al conectarse un jugador | `"Day"`, `"Afternoon"` o `"Night"` según hora actual |

### Sincronización de jugadores nuevos

Cuando un jugador se conecta, el servidor lee el `ClockTime` actual y determina el estado:

```lua
if t >= 6 and t < 14 then  → "Day"
if t >= 14 and t < 18 then → "Afternoon"
else                        → "Night"
```

> **Nota:** Este rango difiere del umbral del MutationService (`isDaytime = t >= 6 y < 18`). Aquí "Afternoon" se distingue de "Day" para los clientes, pero para el MutationService ambos son "día" (ClockTime 6-18).

---

## 10. Tabla de tiempos de ClockTime en el ciclo

| ClockTime | Fase real | Estado del juego |
|---|---|---|
| 14.5 | 2:30 PM | **Día** (plena luz) |
| 14.5 → 17 | Transición 36s | Tween de día → tarde |
| 17 | 5:00 PM | **Tarde** (atardecer naranja) |
| 17 → 0 | Transición 12s | Tween de tarde → noche |
| 0 | Medianoche | **Noche** |
| 0 → 14.5 | Transición 30s | Tween de noche → día |

> El tiempo de juego **no avanza progresivamente** como un día real: **salta directamente** al ClockTime de destino vía tween. La transición de noche a día hace que el ClockTime vaya de 0 a 14.5 en 30 segundos (saltándose la madrugada y mañana).

---

## 11. Impacto del sistema en el resto del juego

### Impacto en MutationService

El `MutationService` escucha `Lighting:GetPropertyChangedSignal("ClockTime")`:
- Detecta cuándo `isDaytime()` cambia (ClockTime cruza los límites 6 o 18).
- **Al pasar a noche**: captura los colores base de los modelos con mutación (`captureBaseline()`).
- **Al pasar a día**: restaura los colores base (`restoreBaseline()`), luego re-aplica estáticos.
- El filtro de partes es **más estricto de día** que de noche.

### Impacto en clientes (clientes que escuchan DayNight)

Los clientes reciben el evento `DayNight` con el nombre de la fase y pueden:
- Cambiar música de fondo
- Mostrar/ocultar elementos de UI (ej: indicador de noche)
- Cambiar efectos de post-procesado
- Activar/desactivar iluminación de interiores

---

## 12. Diagrama del ciclo completo

```
t=0        t=36       t=360      t=372      t=492      t=522      t=780
  │◄──tween─►│         │◄─tween─►│          │◄─tween─►│
  ├──────────┤─────────┼──────────┤──────────┼──────────┤─────────►
  │  DÍA     │         │  TARDE   │          │  NOCHE   │  DÍA...
  │ClockTime │ (plena  │ClockTime │ (atarde- │ClockTime │
  │  14.5    │  luz)   │   17     │  cer)    │    0     │
  │          │         │          │          │          │
[tween 36s] [espera 360s] [tween 12s] [espera 120s] [tween 30s] [espera 300s]
```

> Los tiempos de `task.wait()` son los tiempos de **toda la fase**, incluyendo el tween. El tween ocurre dentro del período de espera, no es adicional.

---

## 13. Propiedades de Lighting no modificadas por el sistema

El DayNightService **no toca**:
- `ExposureCompensation`
- `ClipDistance`
- Efectos dentro de Lighting (Bloom, DepthOfField, etc.)
- `Technology` (FutureIsNow, ShadowMap, Compatibility)

Esto significa que si el juego tiene post-effects configurados en el editor (Bloom, ColorCorrection, etc.), **persisten** durante todo el ciclo.
