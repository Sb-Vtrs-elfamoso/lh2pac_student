"""
Problem 3 : Robust optimization
"""

# %%

from numpy import array
import pickle
from pathlib import Path

from lh2pac.gemseo.discipline import H2TurboFan
from lh2pac.gemseo.utils import draw_aircraft
from lh2pac.gemseo.utils import get_aircraft_data

from gemseo import configure_logger
from gemseo import configure
from gemseo import create_surrogate
from gemseo import create_scenario
from gemseo.algos.design_space import DesignSpace
from gemseo.mlearning.quality_measures.r2_measure import R2Measure
from gemseo.mlearning.quality_measures.rmse_measure import RMSEMeasure
from gemseo.algos.parameter_space import ParameterSpace
from gemseo_umdo.scenarios.umdo_scenario import UMDOScenario
from gemseo_umdo.scenarios.udoe_scenario import UDOEScenario


from lh2pac.marilib.utils import unit

configure(activate_discipline_counters=False, activate_function_counters=False, activate_progress_bar=True, activate_discipline_cache=False, check_input_data=False, check_output_data=False, check_desvars_bounds=False)
# %%
# ## Airplane initialization
# First, we instantiate the discipline:
discipline = H2TurboFan()

# %%
# Then,
# we can have a look at its input names:
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
# We can print the aircraft data:
aircraft_data = get_aircraft_data(discipline)
print(aircraft_data)

# %%
# and draw the aircraft:
draw_aircraft(discipline, "The default A/C")

# %%
# ## Design of experiment
# We want to sample design and uncertain parameters.
# so, we create the design space for design parameters $x$ and uncertain parameters $u$.
configure_logger()
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
        self.add_variable("tgi", l_b=0.25, u_b=0.305, value=0.3)
        self.add_variable("tvi", l_b=0.8, u_b=0.85, value=0.845)
        self.add_variable("sfc", l_b=0.99, u_b=1.03, value=1.0)
        self.add_variable("mass", l_b=0.99, u_b=1.03, value=1.0)
        self.add_variable("drag", l_b=0.99, u_b=1.03, value=1.0)

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
# We run the sampling scenario
scenario.execute({"algo": "OT_OPT_LHS", "n_samples": 30})
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
# ## Robust Optimization
# Now we want to minimize the maximum take-off weight even in the worst case scenario of technological parameters.
# 
# First, we create the design space
class MyDesignSpace(DesignSpace):
    def __init__(self):
        super().__init__(name="design_parameters_space")
        self.add_variable("thrust", l_b=unit.N_kN(100), u_b=unit.N_kN(150), value=optimized_design_parameters['thrust'])
        self.add_variable("bpr", l_b=5, u_b=12, value=optimized_design_parameters['bpr'])
        self.add_variable("area", l_b=120, u_b=200, value=optimized_design_parameters['area'])
        self.add_variable("aspect_ratio", l_b=7, u_b=12, value=optimized_design_parameters['aspect_ratio'])
design_space = MyDesignSpace()

# %%
# we create the parameter space for technological parameters $u$      
class MyUncertainSpace(ParameterSpace):
    def __init__(self):
        super().__init__()
        self.add_random_variable("tgi", "OTTriangularDistribution", minimum=0.25,mode=0.3, maximum=0.305)
        self.add_random_variable("tvi", "OTTriangularDistribution", minimum=0.8,mode=0.845, maximum=0.85)
        self.add_random_variable("sfc", "OTTriangularDistribution", minimum=0.99,mode=1.0, maximum=1.03)
        self.add_random_variable("mass", "OTTriangularDistribution", minimum=0.99,mode=1.0, maximum=1.03)
        self.add_random_variable("drag", "OTTriangularDistribution", minimum=0.99,mode=1.0, maximum=1.03)
        
uncertain_space = MyUncertainSpace()

# %%
# we create a `UMDOScenario` from the surrogate, the
# discipline and the design space and parameter space.
# We used Monte Carlo method to estimate uncertain parameters mean.
disciplines = [surrogate_discipline]
"""
scenario = UMDOScenario(
    disciplines, "DisciplinaryOpt", output_parameters[0], design_space, uncertain_space,
    objective_statistic_name="Margin",
    statistic_estimation="Sampling", statistic_estimation_parameters={"n_samples": 30},
)
"""
scenario = UMDOScenario(disciplines, "DisciplinaryOpt", "mtow", design_space, uncertain_space, 
                        objective_statistic_name="Mean", statistic_estimation="Sampling",
                        statistic_estimation_parameters={
                            "algo": "OT_MONTE_CARLO",
                            "n_samples": 30,
                            "seed": 22
                        }) 

for parameter in  output_parameters[1:] :
    scenario.add_observable(parameter, statistic_name="Mean")

# %%
# we then add constraints
scenario.add_constraint("tofl", constraint_type="ineq", positive=False, value=2200, statistic_name="Margin", factor=0.6)
scenario.add_constraint("vapp", constraint_type="ineq", positive=False, value=unit.mps_kt(137), statistic_name="Margin", factor=0.6)
scenario.add_constraint("vz_mcl", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(300), statistic_name="Margin", factor=0.6)
scenario.add_constraint("vz_mcr", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(0), statistic_name="Margin", factor=0.6)
scenario.add_constraint("oei_path", constraint_type="ineq", positive=True, value=0.011, statistic_name="Margin", factor=0.6)
scenario.add_constraint("ttc", constraint_type="ineq", positive=False, value=unit.s_min(25), statistic_name="Margin", factor=0.6)
scenario.add_constraint("far", constraint_type="ineq", positive=False, value=13.4, statistic_name="Margin", factor=0.6)

# %%
# Now,
# we execute the discipline with a nonlinearly constrained gradient-based optimizer
scenario.set_differentiation_method("finite_differences")
scenario.execute({"algo": "NLOPT_SLSQP", 
                  "max_iter": 50, 
                  "ineq_tolerance": 1e-3,
                  "ctol_abs": 1e-2})

# %%
# ## Visualization
# and plot the history:
scenario.post_process("OptHistoryView", save=True, show=True)

# %%
# We can print and draw the optimized aircraft design:
print(surrogate_discipline.get_input_data())
draw_aircraft(surrogate_discipline.get_input_data(), "The optimized A/C")

# %%
# and execute the discipline with these values:
output_dict = discipline.execute(surrogate_discipline.get_input_data())
for key in output_dict.keys() :
    print(str(key) + ' : ' + str(output_dict[key][0]))

# %%
