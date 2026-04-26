# Sistema de Mutaciones

> **Archivo principal (servidor):** `src/server/Services/MutationService.luau`  
> **Archivo de datos:** `src/shared/Data/MutationCatalog.luau`  
> **Tipo:** ModuleScript (servidor) + ModuleScript compartido  
> **Interacción con el cliente:** `src/client/HUD/IndexManager.client.luau` (preview en Index)

---

## 1. ¿Qué es una Mutación?

Una mutación es una **variante visual y de valor** de un personaje. Todo personaje puede existir en 4 variantes (mutaciones). La mutación afecta:

1. **Apariencia visual** → el modelo se colorea de distinta forma
2. **Multiplicador de generación** → cuánto dinero genera por segundo
3. **Rareza implícita** → las mutaciones más raras generan más

---

## 2. Catálogo de Mutaciones (`MutationCatalog.luau`)

### Tabla completa de mutaciones

| Mutación | Weight | Chance% | GenMultiplier | Tipo visual | Colores |
|---|---|---|---|---|---|
| Normal | 100 | ~11.1% | 1x | Sin cambio | — |
| Gold | 300 | ~33.3% | 2x | Estático | Amarillo dorado |
| Diamond | 300 | ~33.3% | 3x | Estático | Azul celeste |
| Rainbow | 300 | ~33.3% | 10x | Animado (HSV) | Ciclo de colores |

**Peso total:** 100 + 300 + 300 + 300 = **900**

> La chance de Normal es `100/900 = 11.1%`, y cada una de las otras es `300/900 = 33.3%`.

### Colores de Gold

```lua
Colors = {
    Color3.fromRGB(255, 215, 0),   -- oro brillante
    Color3.fromRGB(255, 185, 15),  -- oro medio
    Color3.fromRGB(218, 165, 32),  -- oro oscuro (goldenrod)
}
```

### Colores de Diamond

```lua
Colors = {
    Color3.fromRGB(185, 242, 255),  -- celeste claro
    Color3.fromRGB(120, 220, 255),  -- azul diamante
    Color3.fromRGB(200, 255, 255),  -- casi blanco azulado
}
```

### Rainbow

No tiene colores fijos. Usa el flag `Rainbow = true` → se genera un ciclo HSV animado en tiempo real.

---

## 3. Funciones del MutationCatalog

```lua
MutationCatalog.Get(name)
-- Devuelve la tabla de datos de esa mutación, o nil.

MutationCatalog.RollMutation()
-- Tira un número aleatorio entre 1 y 900 (totalWeight).
-- Recorre MUTATION_ORDER acumulando pesos hasta que roll <= cumulative.
-- Devuelve el nombre de la mutación ("Normal", "Gold", "Diamond", "Rainbow").

MutationCatalog.GetOrder()
-- Devuelve { "Normal", "Gold", "Diamond", "Rainbow" }

MutationCatalog.GetChance(mutationName)
-- Devuelve (weight / totalWeight) * 100 como porcentaje.

MutationCatalog.GetGenMultiplier(mutationName)
-- Devuelve el multiplicador de generación (1, 2, 3 o 10).
-- Devuelve 1 si no existe la mutación.
```

---

## 4. MutationService — Estructura interna

### Variables de estado

```lua
activeEffects  = {}  -- { [model] = { Thread, Stop() } }
staticModels   = {}  -- { [model] = colorsTable } -- modelos con mutación estática activa
baselineColors = {}  -- { [model] = { [part] = Color3 } } -- colores originales antes de mutar
```

---

## 5. Filtrado de partes coloreables (`shouldColorPart`)

Antes de aplicar cualquier color de mutación, el sistema **filtra qué partes del modelo se pueden colorear**. Esto evita arruinar la cara, los ojos y otros detalles pequeños del personaje.

### Condiciones para NO colorear una parte

| Condición | Razón |
|---|---|
| `not part:IsA("BasePart")` | Solo se procesan BaseParts |
| `part.Transparency >= 0.95` | La parte es invisible |
| Nombre exacto en lista negra | Cara/decales |
| Nombre (lowercase) contiene pattern | Rasgos faciales |
| Volumen < 0.001 | Parte micro-invisible |
| *(solo de día)* Color negro (R/G/B < 0.08) y volumen < 0.5 | Detalle pequeño oscuro |
| *(solo de día)* Color blanco (R/G/B > 0.95) y volumen < 0.3 | Detalle pequeño claro |

### Lista negra de nombres exactos

```
"Face", "face", "FaceDecal", "Decal"
```

### Patterns de nombre (substring, case-insensitive)

```
"eye", "pupil", "iris", "retina", "teeth", "tooth", "tongue", "mouth",
"brow", "eyelash", "lash", "glasses", "lens", "spectacle", "nose",
"nostril", "blush", "freckle", "whisker", "moustache", "mustache",
"beard", "eyebrow"
```

> **Importante:** el filtro de color negro/blanco y volumen solo se aplica **durante el día** (`Lighting.ClockTime >= 6 y < 18`). De noche el filtro es más permisivo.

---

## 6. Captura y restauración del baseline de color

Antes de aplicar cualquier mutación, el sistema **captura los colores originales** de todas las BaseParts del modelo para poder restaurarlos.

### `captureBaselineForModel(model)`

```lua
-- Solo captura si no hay baseline ya guardado
local map = {}
for _, part in ipairs(model:GetDescendants()) do
    if part:IsA("BasePart") then
        map[part] = part.Color  -- guarda el Color3 original
    end
end
baselineColors[model] = map
```

### `restoreBaseline()`

```lua
-- Se llama al transicionar a DÍA
for model, map in pairs(baselineColors) do
    if model and model.Parent then
        for part, col in pairs(map) do
            if part.Parent then
                part.Color = col  -- restaura color original
            end
        end
    end
end
baselineColors = {}  -- limpia la tabla
```

---

## 7. Efecto de Mutación Estática (Gold y Diamond)

### `applyStaticColors(model, colors)`

Función interna directa (sin loop). Aplica colores cíclicamente:

```lua
for i, part in ipairs(parts) do
    local colorIdx = ((i - 1) % #colors) + 1
    part.Color = colors[colorIdx]
end
```
Ejemplo con 5 partes y 3 colores de Gold:
- Parte 1 → `colors[1]` (amarillo brillante)
- Parte 2 → `colors[2]` (amarillo medio)
- Parte 3 → `colors[3]` (oro oscuro)
- Parte 4 → `colors[1]` (vuelve al primero)
- Parte 5 → `colors[2]`

### `startStaticMutationEffect(model, colors)`

Captura el baseline, aplica los colores inmediatamente y luego **lanza un `task.spawn` en loop** que mantiene los colores:

```lua
local thread = task.spawn(function()
    while running and model.Parent do
        local parts = getColorableParts(model)
        for i, part in ipairs(parts) do
            local colorIdx = ((i - 1) % #colors) + 1
            if part.Color ~= colors[colorIdx] then
                part.Color = colors[colorIdx]
            end
        end
        task.wait(0.5)  -- revisión cada 0.5 segundos
    end
end)
```

> El loop corre **cada 0.5 segundos** y corrige cualquier parte cuyo color se haya revertido (por ejemplo al transición de día a noche). Los colores de mutación estática se mantienen **siempre**, día y noche.

El efecto se registra en `activeEffects[model]`:
```lua
activeEffects[model] = {
    Thread = thread,
    Stop = function() running = false end,
}
```

---

## 8. Efecto Rainbow

### `startRainbowEffect(model)`

Captura el baseline y lanza un loop que **cicla el tono (hue)** del color HSV:

```lua
local hue = math.random()  -- hue inicial aleatorio entre 0 y 1
local thread = task.spawn(function()
    while running and model.Parent do
        local day = isDaytime()

        -- Al transicionar de NOCHE a DÍA: restaura baseline
        if day and not prevDay then
            local map = baselineColors[model]
            if map then
                for part, col in pairs(map) do
                    if part.Parent then
                        part.Color = col
                    end
                end
                baselineColors[model] = nil
            end
        end
        prevDay = day

        -- Aplica color rainbow a todas las partes coloreables
        local parts = getColorableParts(model)
        hue = (hue + 0.01) % 1  -- incremento de 0.01 por tick
        local color = Color3.fromHSV(hue, 0.85, 1)  -- saturación 85%, brillo 100%
        for _, part in ipairs(parts) do
            if part.Parent then
                part.Color = color
            end
        end
        task.wait(0.03)  -- ~33fps
    end
end)
```

#### Velocidad del ciclo Rainbow

- Incremento de hue: `+0.01` por tick
- Intervalo: `0.03` segundos
- Tiempo para un ciclo completo: `1 / 0.01 * 0.03 = 3 segundos por vuelta completa de colores`

#### Interacción con día/noche en Rainbow

- **Al pasar de NOCHE → DÍA:** restaura los colores del baseline (limpia la mutación visualmente durante el día y la vuelve a re-aplicar inmediatamente en el siguiente tick del loop).
- En la práctica el efecto rainbow continúa durante el día, pero el filter de partes es más estricto de día.

---

## 9. API Pública de MutationService

### `MutationService.ApplyMutationVisual(model, mutationName)`

Función principal para aplicar una mutación a un modelo en el mundo.

```lua
-- Si mutationName es nil o "Normal" → no hace nada
-- Llama StopEffect(model) primero para limpiar efectos anteriores
-- Lee MutationCatalog.Get(mutationName)
-- Si mutData.Rainbow == true → startRainbowEffect(model)
-- Si mutData.Colors y #Colors > 0 → startStaticMutationEffect(model, colors)
-- Si ninguno → no aplica nada (mutación sin datos)
```

### `MutationService.StopEffect(model)`

```lua
-- Llama effect.Stop() si hay efecto activo → pone running=false
-- Limpia activeEffects[model]
-- Limpia staticModels[model]
```

### `MutationService.CleanupModel(model)`

```lua
-- Llama StopEffect(model)
-- Limpia staticModels[model]
-- Usado cuando un personaje es removido del mundo
```

---

## 10. Interacción con el Día/Noche

Esta es la parte más importante de las mutaciones. El sistema **escucha cambios en `Lighting.ClockTime`** y reacciona a las transiciones de día/noche:

```lua
local previousDayState = isDaytime()  -- inicial
local previousClockTime = Lighting.ClockTime

Lighting:GetPropertyChangedSignal("ClockTime"):Connect(function()
    local nowDay = isDaytime()  -- ClockTime >= 6 y < 18

    -- Transición de estado
    if nowDay ~= previousDayState then
        if nowDay then
            -- NOCHE → DÍA: restaura colores originales
            restoreBaseline()
        else
            -- DÍA → NOCHE: captura colores actuales como baseline
            captureBaseline()
        end
        previousDayState = nowDay
    end

    -- Re-aplica colores estáticos si es de día y se acaba de salir de la noche
    if nowDay and previousClockTime < 6 then
        for model, colors in pairs(staticModels) do
            if model and model.Parent then
                applyStaticColors(model, colors)
            end
        end
    end

    previousClockTime = nowTime
end)
```

### Tabla de comportamiento día/noche por tipo de mutación

| Mutación | De Día | De Noche | Al pasar a Día | Al pasar a Noche |
|---|---|---|---|---|
| Normal | Sin cambio | Sin cambio | — | — |
| Gold | Mantiene colores dorados | Mantiene colores dorados | Re-aplica colores estáticos | Captura baseline (aunque ya es dorado) |
| Diamond | Mantiene colores azules | Mantiene colores azules | Re-aplica colores estáticos | Captura baseline |
| Rainbow | Cicla colores (filtro estricto) | Cicla colores (filtro permisivo) | Restaura y re-aplica inmediatamente | Captura baseline |

> **Nota técnica:** El `startStaticMutationEffect` tiene un loop de 0.5s que **siempre re-aplica** los colores, por lo que aunque el sistema restaure el baseline en transición, el loop lo vuelve a poner casi de inmediato. En la práctica Gold y Diamond **siempre se ven con sus colores** independientemente del horario.

---

## 11. Función `isDaytime()`

```lua
local function isDaytime()
    local t = Lighting.ClockTime
    return t >= 6 and t < 18
end
```

- ClockTime va de 0 a 24 (donde 0 = medianoche, 12 = mediodía, 18 = 6pm).
- El umbral exacto: **6:00 AM** hasta **5:59 PM** = día. **6:00 PM** en adelante = noche.

---

## 12. Flujo completo al aplicar una mutación Gold a un personaje

```
ContainerService abre un contenedor y genera un personaje con mutación Gold
         ↓
MutationService.ApplyMutationVisual(model, "Gold")
         ↓
StopEffect(model)  → limpia cualquier efecto anterior
         ↓
MutationCatalog.Get("Gold") → { Colors=[RGB(255,215,0), ...], Rainbow=false }
         ↓
startStaticMutationEffect(model, colorsTable)
    ├── captureBaselineForModel(model)  → guarda colores originales
    ├── staticModels[model] = colors
    ├── getColorableParts(model) → filtra partes
    ├── Aplica colores cíclicamente de inmediato
    └── task.spawn → loop cada 0.5s: re-aplica si alguna parte cambió
         ↓
Lighting.ClockTime cambia (DayNightService tweenea)
    ├── Si noche → captura baseline (aunque ya son colores gold)
    └── Si día → el loop de 0.5s re-aplica gold constantemente
```

---

## 13. Multiplicadores de generación y su impacto

El multiplicador se usa en el cálculo de income del personaje. Si un personaje tiene `GenerationPerSecond = 100`:

| Mutación | Multiplicador | Income real |
|---|---|---|
| Normal | 1x | $100/s |
| Gold | 2x | $200/s |
| Diamond | 3x | $300/s |
| Rainbow | 10x | $1,000/s |

En el Index, la etiqueta `GenLabel` muestra: `charData.GenerationPerSecond * mutMultiplier`.
