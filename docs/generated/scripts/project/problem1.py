"""
Problem 1 : Optimization

Here, the objective was to find a way to minimize the maximum take-off weight `MTOW` of $g:x\mapsto g(x)=f(x,u_{\mathrm{default}})$.

The **design parameters**  $x$ are :

- the engine maximum thrust  (100 kN ≤ thrust ≤ 150 kN, default: 125 kN),
- the engine bypass ratio  (BPR)  (5 ≤ BPR ≤ 12, default: 8.5),
- the wing area  (120 m² ≤ area ≤ 200 m², default: 160 m²),
- the wing aspect ratio  (7 ≤ ar ≤ 12, default: 9.5).

We can rewrite our objectice as $\min_{x}(\mathbb{E}(g(x)_{mtow}))$

We aim to approximate the objective and constraints of the design problem with respect to the design parameters $x$.

In this case, using a surrogate model is very helpfull because it helps to reduce costs and time to find the optimal state of a system.
"""
# %%

from numpy import array
import pickle
from pathlib import Path
import time

from lh2pac.gemseo.discipline import H2TurboFan
from lh2pac.gemseo.utils import draw_aircraft
from lh2pac.gemseo.utils import get_aircraft_data

from gemseo import configure_logger
from gemseo import create_scenario
from gemseo import create_surrogate
from gemseo import import_discipline
from gemseo import configure
from gemseo.algos.design_space import DesignSpace
from gemseo.mlearning.quality_measures.r2_measure import R2Measure
from gemseo.mlearning.quality_measures.rmse_measure import RMSEMeasure
from lh2pac.marilib.utils import unit

configure(activate_discipline_counters=False, activate_function_counters=False, activate_progress_bar=True, activate_discipline_cache=True, check_input_data=False, check_output_data=False, check_desvars_bounds=False)
# %%
# ## Airplane initialization
# First, we instantiate the discipline:
discipline = H2TurboFan()

# %%
# Then, we can have a look at its input names:
discipline.get_input_data_names()

# %%
# output names:
output_parameters = discipline.get_output_data_names()
print(output_parameters)

# %%
# and default input values:
discipline.default_inputs

# %%
# and execute the discipline with these values:
discipline.execute()

# %%
# We can print and draw the aircraft data:
aircraft_data = get_aircraft_data(discipline)
print(aircraft_data)
draw_aircraft(discipline, "The default A/C")

# %%
# ## Optimization of the raw model
# We want to otpimize the model according to its design parameters $x$.
# fisrt, we create the design space for design parameters $x$ :
class MyDesignSpace(DesignSpace):
    def __init__(self):
        super().__init__(name="design_parameters_space")
        self.add_variable("thrust", l_b=unit.N_kN(100), u_b=unit.N_kN(150))
        self.add_variable("bpr", l_b=5, u_b=12)
        self.add_variable("area", l_b=120, u_b=200)
        self.add_variable("aspect_ratio", l_b=7, u_b=12)

design_space = MyDesignSpace()

# %%
# Then,we create a scenario
# to minimize the maximum take-off weight `MTOW`
# under the constraints defined in the use case.
scenario = create_scenario([discipline], "DisciplinaryOpt", "mtow", design_space)
for parameter in  output_parameters[1:] :
    scenario.add_observable(parameter)

scenario.add_constraint("tofl", constraint_type="ineq", positive=False, value=2200)
scenario.add_constraint("vapp", constraint_type="ineq", positive=False, value=unit.mps_kt(137))
scenario.add_constraint("vz_mcl", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(300))
scenario.add_constraint("vz_mcr", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(0))
scenario.add_constraint("oei_path", constraint_type="ineq", positive=True, value=0.011)
scenario.add_constraint("ttc", constraint_type="ineq", positive=False, value=unit.s_min(25))
scenario.add_constraint("far", constraint_type="ineq", positive=False, value=13.4)

# %%
# We execute it with a gradient-free optimizer:
start_time = time.time()
scenario.execute({"algo": "NLOPT_COBYLA", "max_iter": 1000})
print("--- %s seconds ---" % (time.time() - start_time))

# %%
# Lastly,
# we can visualize the optimization history:
scenario.post_process("OptHistoryView", save=False, show=True)

# %%
# We can print the optimized aircraft data:
optimized_design_parameters = discipline.get_input_data()
print(optimized_design_parameters)

# %%
# and draw the aircraft:
draw_aircraft(optimized_design_parameters, "The optimized A/C")

# %%
# However, this approach is too expensive,
# we need to use a surrogate of the model
# to be able to find a good minimization of our objective.
#
# ## Design of experiment
# We create the design space for design parameters $x$ :
configure_logger()
class MyDesignSpace(DesignSpace):
    def __init__(self):
        super().__init__(name="design_parameters_space")
        self.add_variable("thrust", l_b=unit.N_kN(100), u_b=unit.N_kN(150))
        self.add_variable("bpr", l_b=5, u_b=12)
        self.add_variable("area", l_b=120, u_b=200)
        self.add_variable("aspect_ratio", l_b=7, u_b=12)

design_space = MyDesignSpace()

# %%
# Then, we create a `DOEScenario` from this
# discipline and this design space:
disciplines = [discipline]
scenario = create_scenario(
    disciplines, "DisciplinaryOpt", output_parameters[0], design_space, scenario_type="DOE"
)
for parameter in  output_parameters[1:] :
    scenario.add_observable(parameter)

# %%
# Now, we can sample the discipline to get
# 100 evaluations of the airplane parameters :
scenario.execute({"algo": "OT_OPT_LHS", "n_samples": 100})

# %%
# Lastly,
# we export the result to an `IODataset`
dataset = scenario.to_dataset(opt_naming=False)
dataset

# %%
# ## Surrogate modeling
# We create the surrogate discipline using an RBF model
surrogate_discipline = create_surrogate("RBFRegressor", dataset)

# %%
# We assess the regression model
# with the R2 measure for instance:
r2 = R2Measure(surrogate_discipline.regression_model, True)
print('R2 errors')
print('learning measure')
print(r2.compute_learning_measure())
print('validation measure')
print(r2.compute_cross_validation_measure())

# %%
# and with the root mean squared error:
rmse = RMSEMeasure(surrogate_discipline.regression_model, True)
print('RMSE measure')
print('learning measure')
print(rmse.compute_learning_measure())
print('validation measure')
print(rmse.compute_cross_validation_measure())

# %%
# ## Optimization on surrogate model
# Now, we put these elements together in a scenario
# to minimize the maximum take-off weight `MTOW`
# under the constraints definied in the use case.
scenario_surrogate = create_scenario([surrogate_discipline], "DisciplinaryOpt", "mtow", design_space)
for parameter in  output_parameters[1:] :
    scenario.add_observable(parameter)

scenario_surrogate.add_constraint("tofl", constraint_type="ineq", positive=False, value=2200)
scenario_surrogate.add_constraint("vapp", constraint_type="ineq", positive=False, value=unit.mps_kt(137))
scenario_surrogate.add_constraint("vz_mcl", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(300))
scenario_surrogate.add_constraint("vz_mcr", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(0))
scenario_surrogate.add_constraint("oei_path", constraint_type="ineq", positive=True, value=0.011)
scenario_surrogate.add_constraint("ttc", constraint_type="ineq", positive=False, value=unit.s_min(25))
scenario_surrogate.add_constraint("far", constraint_type="ineq", positive=False, value=13.4)

# %%
# before executing it with a gradient-free optimizer:
start_time = time.time()
scenario_surrogate.execute({"algo": "NLOPT_COBYLA", "max_iter": 1000})
print("--- %s seconds ---" % (time.time() - start_time))

# %%
# Lastly,
# we can plot the optimization history:
scenario_surrogate.post_process("OptHistoryView", save=False, show=True)

# %%
# We can print and save the optimized aircraft data:
optimized_surrogate_design_parameters = surrogate_discipline.get_input_data()
print(optimized_surrogate_design_parameters)

with Path("design_parameters.pkl").open("wb") as f:
    pickle.dump(optimized_surrogate_design_parameters, f)

# %%
# and draw the aircraft 
draw_aircraft(optimized_surrogate_design_parameters, "The optimized A/C")

# %%
# ## Errors
# Finally, we verify the error of the surrogate for this optimal design $x^*_{surrogate}$
output_parameters = discipline.get_output_data_names()

raw_model_output = discipline.execute(optimized_surrogate_design_parameters)
surrogate_output = surrogate_discipline.execute(optimized_surrogate_design_parameters)

for param in output_parameters :
    difference = abs(raw_model_output[param][0]-surrogate_output[param][0])
    relative_diffrence = difference / (raw_model_output[param][0]*100)
    print(f"parameter {param} difference of {relative_diffrence:.6f} %")
# %%
# and between the two optimal solutions $x^*_{raw}$ and $x^*_{surrogate}$
input_parameters = ['thrust', 'bpr', 'area', 'aspect_ratio']

for param in input_parameters :
    difference = abs(optimized_surrogate_design_parameters[param][0]-optimized_design_parameters[param][0])
    relative_diffrence = difference / (optimized_design_parameters[param][0]*100)
    print(f"parameter {param} difference of {relative_diffrence:.6f} %")
# %%
