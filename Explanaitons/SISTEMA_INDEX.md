# Sistema de Index (Colección de Personajes)

> **Archivo principal:** `src/client/HUD/IndexManager.client.luau`  
> **Tipo:** LocalScript (cliente)  
> **Template UI:** `ReplicatedStorage.ReplicatedGui.IndexGui`  
> **Template botones:** `ReplicatedStorage.ReplicatedGui.LeftButtons`

---

## 1. ¿Qué es el Index?

El Index es una ventana de colección que muestra **todos los personajes del juego**, organizados por rareza y mutación. El jugador puede ver cuáles ha descubierto, cuántos tiene, cuánto generan por segundo y una **preview 3D animada** de cada uno.

---

## 2. Dependencias y módulos cargados

| Módulo | Ubicación | Uso |
|---|---|---|
| `CharacterCatalog` | `ReplicatedStorage/Shared/Data/` | Datos base de todos los personajes |
| `RarityCatalog` | `ReplicatedStorage/Shared/Data/` | Colores y datos de cada rareza |
| `MutationCatalog` | `ReplicatedStorage/Shared/Data/` | Orden y datos de mutaciones |
| `DebugConfig` | `ReplicatedStorage/Shared/` | Activa/desactiva `debugPrint` |
| `GetInventoryData` | `ReplicatedStorage/Events/` | RemoteFunction → pide inventario al server |
| `InventoryUpdated` | `ReplicatedStorage/Events/` | RemoteEvent → recibe aviso de cambio en inventario |
| `SelectedCharacterChanged` | `ReplicatedStorage/Events/` | RemoteEvent → notifica al server cuál personaje seleccionó el jugador |

### Carpetas de assets
- `ReplicatedStorage/Characters/Models/` → modelos 3D de cada personaje
- `ReplicatedStorage/Characters/Animations/` → animaciones Idle por personaje

---

## 3. Variables de estado globales

```
isOpen          boolean   Si el Index está abierto actualmente
indexGui        Instance  Referencia a la GUI activa (nil si cerrado)
activeViewports table     Lista de ViewportFrames activos para refresh
selectedMutation string   Mutación actualmente seleccionada en la tab bar ("Normal" por defecto)
tabButtonRefs   table     Referencias a los botones de la tab bar: { [mutName] = {Button, Stroke, Colors} }
cachedInventory table     Cache del inventario para no pedir al server en cada render
```

---

## 4. Orden de rareza y mutación

```lua
RARITY_ORDER = { "Common", "Rare", "Epic", "Legendary", "Mythic", "Divine" }
MUTATION_ORDER = MutationCatalog.GetOrder()
-- resultado: { "Normal", "Gold", "Diamond", "Rainbow" }
```

Los personajes se **ordenan por rareza** en el Index (de más común a más raro). Si tienen la misma rareza se ordenan **alfabéticamente**.

---

## 5. Ciclo de vida de la GUI

### 5.1 Apertura (`openIndex`)

1. Si ya está abierto, no hace nada.
2. Destruye cualquier `indexGui` anterior (evita duplicados).
3. Clona `IndexGui` desde `ReplicatedStorage.ReplicatedGui` y lo pone en `PlayerGui`.
4. Resetea `selectedMutation = "Normal"`.
5. Llama `getInventory()` → cachea el inventario via `GetInventoryData:InvokeServer()`.
6. Llama `createTabBar(principalFrame)` → crea la barra de tabs de mutación.
7. Conecta el clic de cada tab a `switchTab(mutName)`.
8. Conecta el botón "CloseButton" del TopBar.
9. Llama `populateIndex()` para renderizar todas las cards.
10. `isOpen = true`.

### 5.2 Cierre (`closeIndex`)

1. Destruye `indexGui`.
2. `isOpen = false`.
3. Limpia `activeViewports`, `cachedInventory`, `tabButtonRefs`.
4. Borra el atributo `SelectedCharacter` del player.

### 5.3 Refresh automático

Cuando el servidor dispara `InventoryUpdated`:
- Si el Index está abierto → `cachedInventory = nil` + `populateIndex()` (re-renderiza todo).
- Si está cerrado → borra `SelectedCharacter` del player.

---

## 6. Jerarquía de la GUI

```
IndexGui (ScreenGui)
└── PrincipalFrame (Frame)
    ├── TopBar (Frame)
    │   ├── CloseButton (TextButton)
    │   └── Counter (TextLabel)  ← muestra "X/Y" personajes descubiertos
    ├── TabBar (Frame) ← creado dinámicamente por createTabBar
    │   ├── UIListLayout (Horizontal, centrado)
    │   ├── UIPadding
    │   ├── Tab_Normal (TextButton)
    │   ├── Tab_Gold (TextButton)
    │   ├── Tab_Diamond (TextButton)
    │   └── Tab_Rainbow (TextButton)
    └── List (Frame) ← se ajusta para dejar espacio a la TabBar
        ├── Template (Frame, Visible=false) ← plantilla de card
        └── [Cards clonadas por cada personaje]
```

### Detalles de la TabBar
- **Altura:** `TAB_BAR_HEIGHT = 38` píxeles.
- Se posiciona **inmediatamente debajo del TopBar** calculando su posición con `topBar.Position + topBar.Size`.
- El `List` se reduce en `TAB_BAR_HEIGHT` píxeles para no solaparse.
- Cada tab tiene `UICorner` con radio 6, `UIStroke` y `UITextSizeConstraint` con máximo 14px.

---

## 7. Colores de cada tab de mutación

| Mutación | Fondo (Bg) | Fondo seleccionado | Texto | Acento |
|---|---|---|---|---|
| Normal | RGB(50,50,60) | RGB(80,80,95) | RGB(200,200,200) | RGB(180,180,190) |
| Gold | RGB(70,55,15) | RGB(120,100,25) | RGB(255,215,0) | RGB(255,215,0) |
| Diamond | RGB(15,50,70) | RGB(30,85,120) | RGB(120,220,255) | RGB(120,220,255) |
| Rainbow | RGB(60,20,55) | RGB(110,40,100) | RGB(255,100,200) | RGB(255,100,200) |

La tab activa muestra `BackgroundColor3 = Selected` y `UIStroke.Thickness = 1.5`. Las inactivas tienen `Thickness = 0`.

---

## 8. Población de cards (`populateIndex`)

### 8.1 Flujo general

1. Limpia `activeViewports`.
2. Si `cachedInventory` es nil, lo pide al server.
3. Lee `PrincipalFrame/List/Template` y `PrincipalFrame/TopBar/Counter`.
4. Oculta el template y destruye todas las cards existentes (excepto Template y elementos de layout).
5. Obtiene la mutación activa (`selectedMutation`) y su multiplicador de generación.
6. Ordena `CharacterCatalog` por rareza (Common → Divine), luego alfabético.
7. Por cada personaje, crea una card.
8. Actualiza `Counter.Text = "X/Y"`.

### 8.2 Lógica de descubrimiento

```
isMutationDiscovered(charInfo, mutationName):
  - Para "Normal": charInfo.Discovered == true
  - Para otras: charInfo.DiscoveredMutations[mutationName] == true
               O el count total (inventario + placed) > 0
```

Si el personaje **no fue descubierto**:
- `Name.Text = "???"`
- `ViewportFrame` se pone semitransparente (`BackgroundTransparency=0.5`, `ImageTransparency=1`)
- La card en sí: `BackgroundTransparency=0.5`, stroke `Transparency=0.6`
- **No** se crea viewport 3D

Si fue descubierto:
- Se muestra nombre y rareza reales
- Se crea la preview 3D en ViewportFrame
- Se agrega label de generación (`GenLabel`)
- Si tiene más de 1, se agrega `CountLabel` con "xN"

### 8.3 Colores del borde de la card (UIStroke y UIGradient)

- `Normal` → usa el `TextColor` de la rareza del personaje.
- `Gold/Diamond/Rainbow` → usa el `Accent` del `TAB_COLORS` de la mutación.

El `UIGradient` va de `Gradient1` (arriba) a `Gradient2` = `RGB(25,25,35)` (abajo).

### 8.4 Labels dinámicas creadas en runtime

**GenLabel** (generación por segundo):
- `Size = UDim2.new(0.5, -3, 0, 14)`
- `Position = UDim2.new(0, 3, 1, -16)` → esquina inferior izquierda de la card
- Texto: `"X/s"` donde X = `charData.GenerationPerSecond * mutMultiplier`
- Fondo: RGB(20,20,30) con transparencia 0.3
- Texto verde: RGB(100,255,100)
- Font: GothamBold, TextScaled, MaxTextSize=12
- UICorner radio 3

**CountLabel** (cantidad en inventario):
- `Size = UDim2.new(0.5, -3, 0, 14)`
- `Position = UDim2.new(0.5, 0, 1, -16)` → esquina inferior derecha
- Texto: `"xN"` donde N = mutations inventory + placed
- Color del texto: `TAB_COLORS[currentMut].Text`
- Misma apariencia visual que GenLabel
- Solo aparece si `count > 0`

---

## 9. Sistema de ViewportFrame

Cada card descubierta tiene un **ViewportFrame** (widget de Roblox que renderiza 3D dentro de una UI).

### 9.1 Configuración del viewport (`setupViewport`)

```
1. Verifica que el modelo exista en modelsFolder (ReplicatedStorage/Characters/Models/)
2. Limpia hijos anteriores: destruye WorldModel y Camera previos
3. Crea WorldModel dentro del viewport
4. Clona el modelo del personaje
5. Ancla todas las BaseParts (Anchored=true, CanCollide=false)
6. Pivota el modelo a CFrame.new(0,0,0) rotado 180° en Y (para mirar de frente)
7. Aplica tint de mutación si no es "Normal" (applyMutationTint)
8. Crea Camera con FOV=50 dentro del viewport
9. Calcula la distancia de la cámara basándose en GetExtentsSize() del modelo:
   - maxDim = max(X,Y,Z) del bounding box
   - dist = maxDim * 2
   - centerY = modelSize.Y * 0.35
   - Camera.CFrame = CFrame.lookAt(
       Vector3(dist*0.5, centerY+0.5, dist*0.7),
       Vector3(0, centerY, 0)
     )
10. Guarda el viewport en activeViewports para el loop de refresh
```

### 9.2 Animación Idle en el viewport

Después de 0.2 segundos (`task.wait(0.2)`):
1. Busca o crea `AnimationController` en el modelo clonado.
2. Busca o crea `Animator` dentro del controller.
3. Busca la carpeta de animaciones: `ReplicatedStorage/Characters/Animations/{characterName}/`.
4. Busca `Idle` dentro de esa carpeta.
5. Carga la animación con `animator:LoadAnimation(idleAnim)`.
6. La pone en loop: `track.Looped = true`, `Priority = Idle`.
7. La reproduce: `track:Play()`.

> Si no existe la carpeta de animaciones o el Idle, simplemente no anima (no hay error).

### 9.3 Loop de refresh (`RunService.Heartbeat`)

```lua
RunService.Heartbeat:Connect(function()
    for _, vp in ipairs(activeViewports) do
        if vp and vp.Parent then
            pcall(function()
                vp:Invalidate()  -- fuerza re-render del viewport
            end)
        end
    end
end)
```

Esto se ejecuta **cada frame** para mantener la preview 3D actualizada aunque la cámara no se mueva. Es necesario para que la animación Idle se vea fluida.

---

## 10. Tint de mutación en el viewport (`applyMutationTint`)

Esta función colorea el modelo **solo en el viewport** (no es la misma función que el `MutationService` del servidor, es una versión local para la UI).

### Filtrado de partes coloreables (mismo criterio que MutationService)

Se saltean:
- Partes con `Transparency >= 0.95`
- Partes con nombre exacto: `Face`, `face`, `FaceDecal`, `Decal`
- Partes con nombre que contenga: `eye, pupil, iris, retina, teeth, tooth, tongue, mouth, brow, eyelash, lash, glasses, lens, spectacle, nose, nostril, blush, freckle, whisker, moustache, mustache, beard, eyebrow`
- Partes con volumen `< MIN_VOLUME = 0.001`
- Partes negras (R<0.08, G<0.08, B<0.08) con volumen < 0.5
- Partes blancas (R>0.95, G>0.95, B>0.95) con volumen < 0.3

### Aplicación del tint

- **Rainbow**: `task.spawn` → loop infinito mientras exista alguna parte, cada 0.03s incrementa `hue + 0.01`, aplica `Color3.fromHSV(hue, 0.85, 1)` a todas las partes.
- **Colores estáticos (Gold/Diamond)**: asigna aleatoriamente uno de los colores de `mutData.Colors` a cada parte.

---

## 11. Sistema de contenedores en el mundo (setupContainer)

El mismo `IndexManager` también configura los contenedores físicos en el Workspace. Cada contenedor en el mundo tiene:

```
ContainerModel (Model)
├── Attribute: "ContainerRarity" = "Common" / "Rare" / etc.
└── ContainerInfo (Folder/Model)
    └── InfoPart (BasePart)
        └── InfoSurface (SurfaceGui)
            └── PrincipalFrame (Frame)
                ├── RarityLabel (TextLabel)
                ├── RaritieDisplayer (TextLabel/TextButton)
                └── List (Frame)
                    ├── UIListLayout o UIGridLayout
                    └── Template (Frame)  ← plantilla de entry
```

### Flujo de `setupContainer`

1. Lee el atributo `ContainerRarity`.
2. Busca `ContainerInfo` con timeout de 3 segundos.
3. Busca `InfoPart > InfoSurface > PrincipalFrame` (o busca PrincipalFrame recursivamente).
4. Configura `RarityLabel.Text` y `.TextColor3` con datos del `RarityCatalog`.
5. Configura `RaritieDisplayer` igual.
6. Por cada personaje de esa rareza:
   - Clona el Template.
   - Calcula el porcentaje de spawn: `(weight / totalWeight) * 100` redondeado.
   - Pone el % en `SpawnWeigth` (label dentro del template).
   - Pone `"$X/s"` en el label `Studs`.
   - Crea un **ViewportFrame** dentro del template con el modelo 3D del personaje (igual que en el Index pero con Camera FOV=50 y posición fija `CFrame.lookAt(0,1.5,4 → 0,1.5,0)`).
7. La Template original queda `Visible=false`.

### Detección de contenedores

El script escanea **tres lugares** al iniciar y también escucha nuevos descendentes:
- `Workspace:GetDescendants()` → todos los modelos en el mundo
- `Workspace/ContainersSpawners:GetDescendants()` → spawners específicos
- `ServerStorage:GetDescendants()` → (modo debug/editor)

Y escucha `DescendantAdded` en Workspace y ContainersSpawners para configurar contenedores que se spawnen en runtime.

---

## 12. Selección de personaje al hacer click

Cuando el jugador hace click en una card:
1. Reproduce sonido de UI si `_G.PlayUISound` está definido: `_G.PlayUISound("Select")`.
2. `player:SetAttribute("SelectedCharacter", characterName)`.
3. Dispara `SelectedCharacterChanged:FireServer(characterName)` al servidor.

El script busca un `GuiButton` dentro de la card con `FindFirstChildWhichIsA("GuiButton", true)`. Si no encuentra ninguno, conecta `InputBegan` directamente en la card.

---

## 13. Flujo completo de una apertura del Index

```
[Jugador presiona IndexButton en LeftButtons]
         ↓
    openIndex()
         ↓
  Clona IndexGui → PlayerGui
         ↓
  getInventory() → InvokeServer("GetInventoryData")
         ↓
  createTabBar(principalFrame)
    → crea Frame "TabBar" de 38px de alto
    → crea 4 botones (Normal/Gold/Diamond/Rainbow)
    → ajusta posición del List
         ↓
  Conecta clicks de tabs → switchTab(mutName)
         ↓
  populateIndex()
    → ordena personajes por rareza
    → por cada personaje:
        ¿descubierto? → card completa + viewport 3D + GenLabel
        ¿no descubierto? → card opaca con "???"
    → Counter.Text = "X/Y"
         ↓
  RunService.Heartbeat → vp:Invalidate() cada frame
         ↓
  [Tab cambia] → switchTab() → selectedMutation = X → populateIndex()
  [InventoryUpdated] → cachedInventory=nil → populateIndex()
  [CloseButton] → closeIndex() → destroy GUI
```

---

## 14. Conexión con el sistema de inventario del servidor

El servidor define la estructura de datos del inventario. El Index espera este formato:

```lua
inventoryData = {
    ["CharacterName"] = {
        Discovered = true/false,         -- si tiene al menos 1 Normal
        Mutations = {                    -- cantidad en backpack
            Gold = 2,
            Diamond = 1,
        },
        PlacedMutations = {              -- cantidad placed en el mapa
            Gold = 1,
        },
        DiscoveredMutations = {          -- si alguna vez obtuvo esta mutación
            Gold = true,
        },
    },
    ...
}
```

`getMutationCount(charInfo, mutationName)` = `Mutations[mutName] + PlacedMutations[mutName]`
