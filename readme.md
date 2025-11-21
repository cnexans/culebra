# Lenguaje de Programación CULEBRA

[![Run Tests](https://github.com/cdgn-coding/culebra/actions/workflows/test.yaml/badge.svg)](https://github.com/cdgn-coding/culebra/actions/workflows/test.yaml)

```
      /^\/^\
    _|__|  O|
\/     /~   \_/ \
 \____|__________/  \
        \_______      \
                `\     \                 \
                  |     |                  \
                 /      /                    \
                /     /                       \\
              /      /                         \ \
             /     /                            \  \
           /     /             _----_            \   \
          /     /           _-~      ~-_         |   |
         (      (        _-~    _--_    ~-_     _/   |
          \      ~-____-~    _-~    ~-_    ~-_-~    /
            ~-_           _-~          ~-_       _-~
               ~--______-~                ~-___-~
```

Este lenguaje minimalista inspirado en Python y Go está diseñado para ser sencillo pero poderoso, con características modernas y estructuras de datos integradas.

## Estado Actual de Implementación

### Características Implementadas ✓
- [x] Expresiones Básicas
  - [x] Expresiones aritméticas (`+`, `-`, `*`, `/`)
  - [x] Expresiones de comparación (`>`, `<`, `>=`, `<=`, `==`, `!=`)
  - [x] Expresiones lógicas (`and`, `or`)
  - [x] Expresiones unarias (negativo `-`, `not`)
  - [x] Expresiones con paréntesis

- [x] Tipos Primitivos
  - [x] Números enteros
  - [x] Cadenas de texto
  - [x] Booleanos
  - [x] Números decimales

- [x] Variables
  - [x] Referencias a identificadores
  - [x] Asignaciones

### Características Pendientes ⏳
- [x] Estructuras de Control
  - [x] Condicionales (`if`, `elif`, `else`)
  - [x] Bucles `while`
  - [x] Bucles `for`

- [x] Funciones
  - [x] Definición de funciones
  - [x] Llamadas a funciones
  - [x] Sentencias `return`

- [x] Estructuras de Datos Complejas
  - [x] Arrays (`[...]`)
  - [ ] Mapas (`{clave: valor, ...}`)
  - [ ] Conjuntos (`{elemento, ...}`)

- [x] Otras Características
  - [x] Manejo de bloques (INDENT/DEDENT)
  - [ ] Valor nulo u Option

- [x] Manejo de Errores
  - [x] Reporte de errores en línea durante parseo
  - [x] Reporte de errores en linea durante interpretación
  - [x] Reporte de errores en linea en chequeo de tipos (Built-in de Python)


- Ejecución
  - [x] Tree-walk interpreter
  - [x] LLVM AOT compiler (Ahead-of-Time)
  - [ ] LLVM Just-in-time compiler

- Herramientas y soporte
  - [ ] Soporte para syntaxis en VS Code con [TextMate](https://code.visualstudio.com/api/language-extensions/syntax-highlight-guide#textmate-grammars)

## Características Principales

### **Tipos Primitivos**

- **Booleanos**: `true`, `false`
- **Enteros**: `123`, `-45`
- **Flotantes**: `3.14`, `-0.56`
- **Cadenas de texto**: `"Hola, mundo!"`, `"""Texto multilínea"""`

### **Tipos Incluidos**

1. **Array**: Lista ordenada de elementos.

   ```python
   numeros = [1, 2, 3]
   ```

2. **Map**: Colección clave-valor.

   ```python
   usuario = {"nombre": "Carlos", "edad": 25}
   ```

3. **Set**: Conjunto de elementos únicos.

   ```python
   numeros_unicos = {1, 2, 3, 3}
   ```

4. **Queue**: Cola para manejo FIFO.

   ```python
   cola = queue()
   cola.enqueue(10)
   valor = cola.dequeue()
   ```

5. **Stack**: Pila para manejo LIFO.

   ```python
   pila = stack()
   pila.push(20)
   valor = pila.pop()
   ```

6. **Priority Queue**: Cola con prioridad.

   ```python
   pq = priority_queue()
   pq.insert(5, priority=1)
   mayor = pq.remove()
   ```

### **Estructuras de Control**

#### **Condicional**

```python
if x > 10:
    print("x es mayor que 10")
elif x == 10:
    print("x es igual a 10")
else:
    print("x es menor que 10")
```

#### **Ciclo for con (declaración, condición y expresión)**

```python
for i = 0; i < 10; i = i + 1:
    print(i)
```

#### **Ciclo for con (condición)**

```python
while x > 0:
    print(x)
    x = x - 1
```

### **Variables**

```python
x = 10
y = "Hola"
z = 3.14
activo = true
```

### **Funciones**

#### **Definición**

```python
def suma(a, b):
    return a + b
```

#### **Llamado**

```python
resultado = suma(5, 7)
```

## Filosofía de Diseño

1. **Simplicidad**: Apuntar a una curva de aprendizaje baja y a tener una sóla forma de hacer las cosas, la correcta.

2. **Estructuras Integradas**: Arrays, mapas, pilas, colas y más para evitar dependencias externas.

3. **Extensibilidad**: Posibilidad de modificar el lenguaje para soportar dominios específicos.

## Compilación y Ejecución

Culebra soporta dos modos de ejecución:

### 1. Modo Interpretado (Tree-walk interpreter)

```bash
# Ejecutar directamente
python -m culebra.interpreter programa.culebra

# REPL interactivo
python -m culebra.interpreter
```

### 2. Modo Compilado (LLVM AOT Compiler)

```bash
# Compilar a ejecutable nativo
python -m culebra.interpreter programa.culebra --compile -o programa

# Ejecutar el programa compilado
./programa

# Ver LLVM IR generado
python -m culebra.interpreter programa.culebra --emit-llvm -o programa.ll

# REPL del compilador (muestra LLVM IR)
python -m culebra.interpreter --compiler
```

**Ventajas del compilador:**
- 15-20x más rápido que el intérprete
- Genera código nativo optimizado
- Compatible con bibliotecas C externas
- Extensible con funciones personalizadas en C

Ver [culebra/compiler/README.md](culebra/compiler/README.md) para más detalles.

## Ejemplo Completo

```python
# Programa ejemplo
numeros = [1, 2, 3, 4, 5]
suma_total = 0

for i = 0; i < len(numeros); i = i + 1:
    suma_total = suma_total + numeros[i]

if suma_total > 10:
    print("La suma es mayor que 10")
else:
    print("La suma es menor o igual a 10")

def cuadrado(x):
    return x * x

print(cuadrado(5))
```
