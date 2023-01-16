# gethighs

A Python interface to using HiGHS executable files on Pyomo.

## Current alternatives

### Appsi solvers

Pyomo has currently HiGHS appsi solver implemented, which works very well for systems in which *highspy* is available (and stable).

You can install highspy directly from pip (make sure pyomo and pybind11 are installed)

```
pip install highspy
```

And import the appsi solver from the following path:

```python
from pyomo.contrib.appsi.solvers import Highs
```

Use it as any pyomo solver from solver factory and be happy! Unless you have some trouble with highspy... And you might, as I did.

If that's your case, keep with me a few more lines.

## Downloading executables

First, make sure you have a highs executable file available in your computer.

You can find HiGHS static executable files pre-compiled for several systems on [this link](https://github.com/JuliaBinaryWrappers/HiGHS_jll.jl/releases).

More information is available on [HiGHS github page](https://github.com/ergo-code/highs).

After dowloading the executables, it helps if they are included in system (or user) path. You might need no reinitialize your computer after this.

## Installing gethighs

gethighs is a small Python package which I developed for using HiGHS directly from executable files via the Pyomo interface. You can install it via pip + the github link:

``pip install -e git+https://github.com/bruscalia/gethighs#gethighs``

And also use it *almost* as a native pyomo solver.

## Usage

You can see more details in the [example notebook](./examples/simple_ip.ipynb).

Consider this simple example:

$$
\begin{align}
    \text{maximize}~~ & 5 x_{1} + 4 x_{2} \\
    \text{subject to}~~ & 2 x_{1} + 3 x_{2} \leq 12 \\
    & 2 x_{1} + x_{2} \leq 6 \\
    & x_{i} \geq 0 & \forall \; i \in \{  1, 2 \} \\
    & x_{i} \in \mathbb{Z} & \forall \; i \in \{  1, 2 \}
\end{align}
$$

Import the required libraries:

```python
import pyomo.environ as pyo
from gethighs import HiGHS
```

Instantiate the model.

```python
# Initialize model
model = pyo.ConcreteModel()

# Set
model.I = pyo.Set(initialize=[1, 2])

# Variables
model.x = pyo.Var(model.I, within=pyo.NonNegativeIntegers)

# Constraints
model.c1 = pyo.Constraint(expr=2 * model.x[1] + 3 * model.x[2] <= 12)
model.c2 = pyo.Constraint(expr=2 * model.x[1] + model.x[2] <= 6)

# Objective
model.obj = pyo.Objective(expr=5 * model.x[1] + 4 * model.x[2], sense=pyo.maximize)
```

Instantiate and configure the solver.

```python
solver = HiGHS(time_limit=10, mip_heuristic_effort=0.2, mip_detect_symmetry="on")
```

Solve the model.

```python
results = solver.solve(model)
print(results)
```

```
status: Optimal
primal_solutions: Feasible
objective: 18.0
```

```python
model.x.display()
```

```
    x : Size=2, Index=I
    Key : Lower : Value : Upper : Fixed : Stale : Domain
      1 :     0 :   2.0 :  None : False : False : NonNegativeIntegers
      2 :     0 :   2.0 :  None : False : False : NonNegativeIntegers
```

## Contact

You can reach out to me at: bruscalia12@gmail.com
