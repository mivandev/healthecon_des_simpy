#!/usr/bin/env python
# coding: utf-8

# # Simple health economic DES model with Python

# A very simple model to serve as an exploration of creating health economic Discrete-Event Simulation (DES) models in
# Python using SimPy library. The clinical context of the model is as follows:
# * During a cycle of treatment, patients can either die (p = 0.15) or experience a full cycle of treatment without any other events occurring.
# * Patients can receive up to five cycles of treatment.
# * A full cycle causes a longer delay or timeout compared to dying during a cycle. These timeouts are drawn from a Gamma distribution.
# * After surviving the maximum number of treatment cycles, patients will enter a follow up phase, in which patients can also die.
#
# The health economic context is as follows:
# * Each cycle of treatment incurs 5000 euro initially and 250 euro per day.
# * Followup costs 3500 euro per patient as a lumpsum.
# * Health-related quality of life (QoL) in the treatment phase is 0.7 as expressed over the duration of one year.
# * QoL in the followup phase is 0.8 as expressed over the duration of one year.
#
# Furthermore, all patients are simulated at `t = 0`, so the interarrival time = 0.
# Note that the model currently only represents one comparator.
# So for an actual cost-effectiveness analysis, another comparator must be added, but this is very straightforward.

# Three classes are created for the model: 1) a class `g` contains all constants,
# 2) a `Patient` class in which attributes of patients are set and 3) a `Model` class containing the model structure
# and Patient Generator method. The model is run by creating an instance of `Model` and
# subsequently executing the `run()` method of that `Model` instance. To accomodate the need to conduct multiple runs,
# this is performed in a for loop.

# Importing libraries and setting the random seed for reproducibility.
import random
from random import seed
import numpy as np
import pandas as pd
import simpy

seed(123)


class g:
    max_cycles = 5  # Maximum number of treatment cycles per patient
    prob_death = 0.15  # Probability of dying during one cycle per patient
    n_patients = 10000  # Number of patients to simulate
    c_treatment_init = 5000
    c_treatment_daily = 250
    c_followup = 3500
    u_treatment = 0.7
    u_followup = 0.8
    days_per_year = 365.2422
    sim_duration = simpy.core.Infinity
    number_of_runs = 1


class Patient:
    def __init__(self, patient_id):
        """Initializing attributes of Patients.
        Of course these can be expanded to more accurately reflect patient heterogeneity."""
        self.patient_id = patient_id
        self.state = 'Alive'
        self.treatment_cycles = 0
        self.cost = 0
        self.utility = 0


class Model:
    def __init__(self, run_number):
        self.env = simpy.Environment()
        self.patient_counter = 0
        self.run_number = run_number

    def generate_patients(self):
        """The method that generates patients.
        """
        yield self.env.timeout(0)  # SimPy processes cannot be 'empty'
        # Main generator loop that terminates when enough patients are simulated or
        # when until is reached

        self.run_number += 1
        while self.env.now < g.sim_duration and self.patient_counter < g.n_patients:
            self.patient_counter += 1
            # Create a new instance of the Patient class
            pat = Patient(patient_id=self.patient_counter)

            # Use the SimPy environment and the enter_treatment and enter_followup methods
            # with this patient
            self.env.process(self.set_care_pathway(pat))

    def run(self):
        self.env.process(self.generate_patients())
        self.env.run(until=g.sim_duration)

        #################### START SECTION: MODEL STRUCTURE ####################

    def set_care_pathway(self, patient):
        """ Method that models the treatment phase.
        """

        #### TREATMENT PHASE ####
        while patient.treatment_cycles < g.max_cycles and patient.state == 'Alive':
            patient.treatment_cycles += 1

            # First, the event that occurs during a cycle is determined.
            rand = random.uniform(0, 1)
            if rand < g.prob_death:
                ##### EVENT: DEATH

                # CHANGE PATIENT'S STATE TO DEAD
                patient.state = 'Dead'

                # SAMPLE A TIME-TO-EVENT
                time_to_death = np.random.gamma(1.5, 3, 1)

                # TIMEOUT EQUAL TO THE TIME-TO-EVENT
                yield self.env.timeout(time_to_death)

                # INCREMENT ACCUMULATED COSTS AND UTILITY
                patient.cost = self.increment_cost(patient, time_to_death)
                patient.utility = self.increment_utility(time_to_death, g.u_treatment)

            else:
                ##### EVENT: FULL CYCLE
                time_to_full_cycle = np.random.gamma(3, 10, 1)
                yield self.env.timeout(time_to_full_cycle)
                patient.cost = self.increment_cost(patient, time_to_full_cycle)
                patient.utility = self.increment_utility(time_to_full_cycle, g.u_treatment)

            # SAVE DATA AT THE END OF EACH CYCLE
            self.save_data(patient, 'treatment')

        #### FOLLOWUP PHASE ####
        if patient.state == 'Alive':
            time_in_folllowup = np.random.gamma(2, 15, 1)
            yield self.env.timeout(time_in_folllowup)
            patient.utility = self.increment_utility(time_in_folllowup, g.u_followup)
            patient.cost = g.c_followup
            self.save_data(patient, 'followup')

            #################### END SECTION: MODEL STRUCTURE ####################

    #################### START SECTION: HELPER METHODS ####################

    def save_data(self, patient, phase):
        """Append a list of outcomes of interest as specified here to a list that
        is created outside the Patient class. This method should be called whenever it
        is appropriate to save data. E.g., each treatment cycle.
        Note, appending a list to a list and converting the final list once to a dataframe is much more efficient
        than appending directly to a pd dataframe."""
        output_list.append(
            [patient.patient_id, patient.state, patient.treatment_cycles, phase, patient.cost, patient.utility,
             self.run_number, self.env.now])

    @staticmethod
    def increment_cost(patient, duration):
        """Helper method to increment the cost attribute of Patient"""
        cost_increment = int(duration) * g.c_treatment_daily
        if patient.treatment_cycles == 1:
            cost_increment += g.c_treatment_init
        return cost_increment

    @staticmethod
    def increment_utility(duration, utility):
        """Helper method to increment the utility attribute of Patient"""
        utility_increment = duration * (utility / g.days_per_year)
        return utility_increment

    #################### END SECTION: HELPER METHODS ####################


# Empty list to store outcomes of interest in. Used by the Patient.save_data() method.
output_list = []

# Running the model for the required amount of runs and printing progress.
for run in range(g.number_of_runs):
    print("Run ", run + 1, " of ", g.number_of_runs, sep="")
    my_model = Model(run)
    my_model.run()
    print()

output_df = pd.DataFrame(output_list,
                         columns=['patient_id', 'state', 'treatment_cycle', 'phase', 'cost', 'utility', 'run_number',
                                  'simulation_time'])
output_df[['utility', 'simulation_time']] = output_df[['utility', 'simulation_time']].astype(float)
# print(output_df)

print(output_df.loc[output_df['patient_id'] == 7])

# Transform the dataframe so that one row equals one patient where:
# Costs and utility are summed, simulation_time equals the latest simulation_time,
# State equals the final value of state, and treatment cycle equals the maximum value

# summary_df = output_df.loc[output_df.groupby('patient_id')['simulation_time'].idxmax()]
summary_df = pd.DataFrame()
summary_df[['patient_id', 'state', 'treatment_cycles_rec', 'simulation_time']] = \
    output_df[['patient_id', 'state', 'treatment_cycle', 'simulation_time']].loc[
        output_df.groupby(['patient_id', 'run_number'])['simulation_time'].idxmax()]


# Function to sum costs and utility for each patient
def calculate_on_group(x):
    return pd.Series(x.sum(), index=x.index)


summary_df['cost'] = output_df.groupby(['patient_id', 'run_number'])['cost'].apply(calculate_on_group)
summary_df['utility'] = output_df.groupby(['patient_id', 'run_number'])['utility'].apply(calculate_on_group)

summary_df.head(n=10)

print(summary_df[['cost', 'utility', 'treatment_cycles_rec']].describe())

# # Checking distributions
# # Just some code to check the values of distributions for the model
# import matplotlib.pyplot as plt
# import scipy.special as sps

# shape = 1.5
# scale = 3
# x = np.random.gamma(shape, scale, 10000)

# count, bins, ignored = plt.hist(x, 50, density=True)
# y = bins**(shape-1)*(np.exp(-bins/scale) /
#                      (sps.gamma(shape)*scale**shape))
# plt.plot(bins, y, linewidth=2, color='r')
# # plt.show()
