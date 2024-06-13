# Surrogate modeling and optimization

Here, the objective was to create a surrogate model of $g:x\mapsto g(x)=f(x,u_{\mathrm{default}})$
to approximate the objective and constraints of the design problem
with respect to the design parameters $x$.

Then, this surrogate model is used in an optimization process
to minimize the objective whilst ensuring the constraints
by varying the design parameters.

## Design of experiment
We created an experimental design by creating a Design Space which specifies the design parameters such as `thrust`, `bypass ratio` (bpr), `area`, and `aspect ratio`, with defined lower and upper bounds.

We created a scenario using these design parameters to calculate the outputs of the original model, which is executed using a Latin Hypercube Sampling (LHS) method to gather 100 evaluations of aircraft parameters.

## Surrogate model
Then, these samples are used to approximate the relationship between input design parameters and output objectives or constraints without repeatedly executing computationally expensive models. Here, a surrogate model is created using a Radial Basis Function (RBF) regressor trained on the dataset generated from the design of experiment. 

The performance of the surrogate model is evaluated using the R2 and root mean squared error (RMSE) measures to assess both learning accuracy and cross-validation performance.

These metrics help confirm the model's predictive capability and generalization across unseen data.

## Otpimization on surrogate
Finally, we optimized the surrogate model with constraints and objectives defined by the aircraft design requirements, such as takeoff field length, approach speed, and vertical climb rates.

The optimization employs a gradient-free method (NLOPT COBYLA) to adjust the design parameters with the aim of minimizing the primary objective (maximum takeoff weight, MTOW) while adhering to operational constraints

The optimization history is visualized to analyze the progression of the design parameters throughout the iterative process.

This surrogate-based approach effectively reduces computational demands and expedites the design process by allowing for rapid iterations on the design parameters with a reliable estimate of objective and constraint behaviors.
