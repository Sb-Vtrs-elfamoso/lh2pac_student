
<!--
 DO NOT EDIT.
 THIS FILE WAS AUTOMATICALLY GENERATED BY mkdocs-gallery.
 TO MAKE CHANGES, EDIT THE SOURCE PYTHON FILE:
 "docs/scripts/project/problem3.py"
 LINE NUMBERS ARE GIVEN BELOW.
-->

!!! note

    Click [here](#download_links)
    to download the full example code


Problem 3 : Robust optimization

<!-- GENERATED FROM PYTHON SOURCE LINES 6-28 -->

```{.python }

from numpy import array
import pickle
from pathlib import Path

from lh2pac.gemseo.discipline import H2TurboFan
from lh2pac.gemseo.utils import draw_aircraft
from lh2pac.gemseo.utils import get_aircraft_data

from gemseo import configure_logger
from gemseo import create_surrogate
from gemseo import import_discipline
from gemseo import configure
from gemseo.algos.design_space import DesignSpace
from gemseo.mlearning.quality_measures.r2_measure import R2Measure
from gemseo.mlearning.quality_measures.rmse_measure import RMSEMeasure
from gemseo.algos.parameter_space import ParameterSpace
from gemseo_umdo.scenarios.umdo_scenario import UMDOScenario

from lh2pac.marilib.utils import unit

configure(activate_discipline_counters=False, activate_function_counters=False, activate_progress_bar=True, activate_discipline_cache=False, check_input_data=False, check_output_data=False, check_desvars_bounds=False)
```

<!-- GENERATED FROM PYTHON SOURCE LINES 29-31 -->

## Airplane initialization
First, we instantiate the discipline:

<!-- GENERATED FROM PYTHON SOURCE LINES 31-33 -->

```{.python }
discipline = H2TurboFan()

```

<!-- GENERATED FROM PYTHON SOURCE LINES 34-36 -->

Then,
we can have a look at its input names:

<!-- GENERATED FROM PYTHON SOURCE LINES 36-38 -->

```{.python }
discipline.get_input_data_names()

```

<!-- GENERATED FROM PYTHON SOURCE LINES 39-40 -->

output names:

<!-- GENERATED FROM PYTHON SOURCE LINES 40-43 -->

```{.python }
output_parameters = discipline.get_output_data_names()
print(output_parameters)

```

<!-- GENERATED FROM PYTHON SOURCE LINES 44-45 -->

and default input values:

<!-- GENERATED FROM PYTHON SOURCE LINES 45-47 -->

```{.python }
discipline.default_inputs

```

<!-- GENERATED FROM PYTHON SOURCE LINES 48-49 -->

and execute the discipline with these values:

<!-- GENERATED FROM PYTHON SOURCE LINES 49-51 -->

```{.python }
discipline.execute()

```

<!-- GENERATED FROM PYTHON SOURCE LINES 52-53 -->

We can print the aircraft data:

<!-- GENERATED FROM PYTHON SOURCE LINES 53-56 -->

```{.python }
aircraft_data = get_aircraft_data(discipline)
print(aircraft_data)

```

<!-- GENERATED FROM PYTHON SOURCE LINES 57-58 -->

and draw the aircraft:

<!-- GENERATED FROM PYTHON SOURCE LINES 58-60 -->

```{.python }
draw_aircraft(discipline, "The default A/C")

```

<!-- GENERATED FROM PYTHON SOURCE LINES 61-63 -->

## Design of experiment
we activate the logger.

<!-- GENERATED FROM PYTHON SOURCE LINES 63-93 -->

```{.python }
configure_logger()
# we create the design space for design parameters $x$
with Path("design_parameters.pkl").open("rb") as f:
    optimized_design_parameters = pickle.load(f)

print(optimized_design_parameters)

class MyDesignSpace(DesignSpace):
    def __init__(self):
        super().__init__(name="design_parameters_space")
        self.add_variable("thrust", l_b=unit.N_kN(100), u_b=unit.N_kN(150), value=optimized_design_parameters['thrust'])
        self.add_variable("bpr", l_b=5, u_b=12, value=optimized_design_parameters['bpr'])
        self.add_variable("area", l_b=120, u_b=200, value=optimized_design_parameters['area'])
        self.add_variable("aspect_ratio", l_b=7, u_b=12, value=optimized_design_parameters['aspect_ratio'])

design_space = MyDesignSpace()

# we create the parameter space for technological parameters $u$      
class MyUncertainSpace(ParameterSpace):
    def __init__(self):
        super().__init__()
        self.add_random_variable("tgi", "SPTriangularDistribution", minimum=0.25,mode=0.3, maximum=0.305)
        self.add_random_variable("tvi", "SPTriangularDistribution", minimum=0.8,mode=0.845, maximum=0.85)
        self.add_random_variable("sfc", "SPTriangularDistribution", minimum=0.99,mode=1.0, maximum=1.03)
        self.add_random_variable("mass", "SPTriangularDistribution", minimum=0.99,mode=1.0, maximum=1.03)
        self.add_random_variable("drag", "SPTriangularDistribution", minimum=0.99,mode=1.0, maximum=1.03)
        
uncertain_space = MyUncertainSpace()


```

<!-- GENERATED FROM PYTHON SOURCE LINES 94-96 -->

Thirdly,
we create a `DOEScenario` from this discipline and this design space:

<!-- GENERATED FROM PYTHON SOURCE LINES 96-105 -->

```{.python }
disciplines = [discipline]
scenario = UMDOScenario(
    disciplines, "DisciplinaryOpt", output_parameters[0], design_space, uncertain_space,
    objective_statistic_name="Mean", statistic_estimation="Sampling", statistic_estimation_parameters={"n_samples": 50},
)

for parameter in  output_parameters[1:] :
    scenario.add_observable(parameter, statistic_name="Mean")

```

<!-- GENERATED FROM PYTHON SOURCE LINES 106-107 -->

adding constraints

<!-- GENERATED FROM PYTHON SOURCE LINES 107-115 -->

```{.python }
scenario.add_constraint("tofl", constraint_type="ineq", positive=False, value=2200, statistic_name="Mean")
scenario.add_constraint("vapp", constraint_type="ineq", positive=False, value=unit.mps_kt(137), statistic_name="Mean")
scenario.add_constraint("vz_mcl", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(300), statistic_name="Mean")
scenario.add_constraint("vz_mcr", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(0), statistic_name="Mean")
scenario.add_constraint("oei_path", constraint_type="ineq", positive=True, value=0.011, statistic_name="Mean")
scenario.add_constraint("ttc", constraint_type="ineq", positive=False, value=unit.s_min(25), statistic_name="Mean")
scenario.add_constraint("far", constraint_type="ineq", positive=False, value=13.4, statistic_name="Mean")

```

<!-- GENERATED FROM PYTHON SOURCE LINES 116-118 -->

Now,
we execute the discipline with a gradient-free optimizer

<!-- GENERATED FROM PYTHON SOURCE LINES 118-120 -->

```{.python }
scenario.execute({"algo": "NLOPT_COBYLA", "max_iter": 30})

```

<!-- GENERATED FROM PYTHON SOURCE LINES 121-122 -->

plot the history:

<!-- GENERATED FROM PYTHON SOURCE LINES 122-123 -->

```{.python }
scenario.post_process("OptHistoryView", save=True, show=True)
```

<!-- GENERATED FROM PYTHON SOURCE LINES 126-127 -->

We can print the aircraft data:

<!-- GENERATED FROM PYTHON SOURCE LINES 127-129 -->

```{.python }
print(discipline.get_input_data())

```

<!-- GENERATED FROM PYTHON SOURCE LINES 130-131 -->

and draw the aircraft:

<!-- GENERATED FROM PYTHON SOURCE LINES 131-133 -->

```{.python }
draw_aircraft(discipline.get_input_data(), "The optimized A/C")

```


**Total running time of the script:** ( 0 minutes  0.000 seconds)

<div id="download_links"></div>



[:fontawesome-solid-download: Download Python source code: problem3.py](./problem3.py){ .md-button .center}

[:fontawesome-solid-download: Download Jupyter notebook: problem3.ipynb](./problem3.ipynb){ .md-button .center}


[Gallery generated by mkdocs-gallery](https://mkdocs-gallery.github.io){: .mkd-glr-signature }