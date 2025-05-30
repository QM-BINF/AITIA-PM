from typing import Tuple
import pandas as pd
import numpy as np
import tqdm
import copy

class Inference:

    def __init__(self, file_path, pb) -> None:
        self.source = pd.read_csv(file_path)
        self.pb = pb
        
        self.dict_by_obs = {}
        self.alphabet = []
        self.events = 0
        self.traces = 0
        self.max_time = 0

        self.hypotheses = []
        self.prima_facie = {}

        self.populate_vars()

    def populate_vars(self) -> None:
        """
        Read time series data from file and get *dict_by_obs*, and *alphabet*.
        """
        self.events = len(self.source.index)
        self.traces = len(self.source['case:concept:name'].unique())

        for index, row in self.generate_iterator(self.source.iterrows(), "Processing time series data"):
            case, obs, t = row

            # Populate dict_by_obs
            # Overview of all timestamps by observation
            # (In case you need to know when specific observations were made)
            if obs not in self.dict_by_obs:
                self.dict_by_obs[obs] = {case: [t]}
            else:
                if case in self.dict_by_obs[obs]:
                    self.dict_by_obs[obs][case].append(t)
                else:
                    self.dict_by_obs[obs][case] = [t]

            # Populate the alphabet
            # Overview of all different observations made (states)
            if obs not in self.alphabet:
                self.alphabet.append(str(obs))
            
            # Set max time
            self.max_time = self.source.iloc[-1,2]

    def generate_hypotheses_for_effects(self, causes, effects) -> None:
        """
        Generates hypotheses for all effects. A hypothesis is of form:
            (cause, effect)

        Parameters:
            causes:     a variable or set of variables
            effects:   a list of possible effects
        """
        self.hypotheses = [(cause, effect) for effect in effects for cause in causes if cause != effect]

    def test_for_prima_facie(self) -> None:
        """
        For a hypothesis of form (c,e), test whether c is a potential cause of e.
        """
        for hypothesis in self.generate_iterator(self.hypotheses, "Testing for prima facie conditions"):
            cause, effect = hypothesis

            c_and_e, c_trues, e_trues = self.test_cause_effect_pair(cause, effect)

            if self.is_prima_facie(c_and_e, c_trues, e_trues):
                # Add entry to Prima Facie dict containing all causes and their time windows
                if effect not in self.prima_facie:
                    self.prima_facie[effect] = [cause]
                else:
                    self.prima_facie[effect].append(cause)

    def test_cause_effect_pair(self, cause, effect) -> Tuple[int, int, int]:
        """
        Get the amount of traces where the cause occurred, the effect occurred and where the cause occurred before the effect
        """

        subset = copy.deepcopy(self.source[self.source['observation'].isin([cause, effect])])

        c_traces = subset[subset['observation'] == cause]['case:concept:name'].unique()
        e_traces = subset[subset['observation'] == effect]['case:concept:name'].unique()
        c_e_cases = set(c_traces).intersection(e_traces)

        c_before_e = 0

        for case in c_e_cases:
            trace = subset[subset['case:concept:name'] == case]
            obs_values = trace['observation'].values
            time_values = trace['time:timestamp'].values
            if effect in obs_values:
                c_times = time_values[obs_values == cause]
                e_times = time_values[obs_values == effect]
                if np.min(c_times) <= np.max(e_times):
                    c_before_e += 1

        return(c_before_e, len(c_traces), len(e_traces))

    def is_prima_facie(self, c_and_e, c_trues, e_trues) -> bool:
        """
        Determines whether c is a prima facie cause of e.

        Parameters:
            c_and_e:    number of traces where c occurred before e
            c_trues:     number of traces containing c
            e_trues:     number of traces containing e
        """
        if c_trues == 0:
            return(False)
        
        return (c_and_e / c_trues > e_trues / self.traces)

    def calculate_average_epsilons(self, target_file) -> None:
        """
        Get the epsilon values for all relationships

        Parameters:
            target_file: the output file to write results to.
        """
        with open(target_file, mode='w') as f:
            f.write(f"cause,effect,epsilon")

            for effect in self.prima_facie:
                for cause in self.generate_iterator(self.prima_facie[effect], desc = "Calculating Epsilon values"):
                    epsilon_avg = self.get_epsilon_average(effect, cause)
                    f.write("\n")
                    f.write(f"{cause},{effect},{epsilon_avg}")

    def get_epsilon_average(self, effect, cause) -> float:
        """
        Calculates the epsilon value for a given hypothesis.

        Parameters:
            effect: the variable representing the effect.
            cause: the variable representing the prima facie cause
        """
        other_causes = [x for x in self.prima_facie[effect] if x != cause]

        if len(other_causes) != 0:
            eps_x = 0
            for x in other_causes:
                # Sum epsilon_x for the other causes
                eps_x += self.calculate_probability_differences(effect, cause, x)

            return(eps_x / len(other_causes))
        
        return None

    def calculate_probability_differences(self, effect, cause, x) -> float:
        """
        Calculates the epsilon_x value for a specific effect, cause, and x.
        """

        c_and_x = 0
        c_and_x_and_e = 0
        not_c_and_x = 0
        not_c_and_x_and_e = 0

        # Because every counter requires x in the trace, only iterate over cases in which x is present.
        subset = copy.deepcopy(self.source[self.source['observation'].isin([cause, effect, x])])
        x_cases = subset[subset['observation'] == x]['case:concept:name'].unique()

        for case in x_cases:
            trace = subset[subset['case:concept:name'] == case]
            obs_values = trace['observation'].values
            time_values = trace['time:timestamp'].values

            # counts for c and x
            if np.any(obs_values == cause) and np.any(obs_values == x):
                c_and_x += 1
                if np.any(obs_values == effect):
                    c_times = time_values[obs_values == cause]
                    x_times = time_values[obs_values == x]
                    e_times = time_values[obs_values == effect]

                    if np.min(c_times) <= np.max(e_times) and np.min(x_times) <= np.max(e_times):
                        c_and_x_and_e += 1

            # counts for not c only x
            if np.all(obs_values != cause) and np.any(obs_values == x):
                not_c_and_x += 1
                if np.any(obs_values == effect):
                    x_times = time_values[obs_values == x]
                    e_times = time_values[obs_values == effect]

                    if np.min(x_times) <= np.max(e_times):
                        not_c_and_x_and_e += 1

        # Return value: P(e|c ∧ x) − P(e|¬c ∧ x)
        # or e and c and x / c and x - e not c and x / not c and x
        if c_and_x == 0 or not_c_and_x == 0:
            return 0
        else:
            return(c_and_x_and_e / c_and_x - not_c_and_x_and_e / not_c_and_x)

    #########
    # Other #
    #########

    def generate_iterator(self, iter, desc = None):
        """
        Displays a progress bar with description if set in the initialisation of the instance.
        """
        if not self.pb:
            return iter
        else:
            return tqdm.tqdm(iter,  desc = desc)

    @staticmethod
    def get_ands(c_trues, x_trues, window) -> list:
        """
        Gets the timepoints where both c and x are true, related to the time windows of c and x and respecting the case to which they belong.
        It is assumed these time windows are the same for simplicity's sake.

        Parameters:
            c_trues: timepoints where c is true containing lists of cases observed at that point.
            x_trues: timepoints where x is true containing lists of cases observed at that point.
            window (r,s): the start and end times of the time window.
        
        Returns:
            List of tuples describing time window overlaps between c and x taking into account the case notion.
        """
        and_list = []
        r, s = window
        range = s - r

        for t in c_trues:
            c_cases = c_trues[t]
            window1 = (t + r, t + s)
            x_candidates = [key for key in x_trues if key >= t - range and key <= t + range]
            for cand in x_candidates:
                x_cases = x_trues[cand]
                intersection = [c for c in c_cases if c in x_cases]
                window2 = (cand + r, cand + s)
                overlap = Inference.get_overlap(window1, window2)
                if overlap != None and len(intersection) != 0:
                    and_list.append((overlap, intersection))
        
        return(and_list)

    @staticmethod
    def get_nots(c_trues, x_trues, window) -> list:
        """
        Gets the timepoints where c is false yet x is true, related to the time windows of c and x and the case they belong to.
        It is assumed these time windows are the same for simplicity's sake.

        Parameters:
            c_trues: timepoints where c is true.
            x_trues: timepoints where x is true.
            window: a tuple containing the start and end times of the time window.
        """
        not_list = []
        r, s = window
        range = s - r

        for t in c_trues:
            c_cases = c_trues[t]
            window1 = (t + r, t + s)
            x_candidates = [key for key in x_trues if key >= t - range and key <= t + range]
            for cand in x_candidates:
                x_cases = x_trues[cand]
                intersection = [c for c in c_cases if c in x_cases]
                window2 = (cand + r, cand + s)

                if len(intersection) == 0:
                    not_list.append((window2, intersection))
                
                only_x = Inference.get_only_x(window1, window2)
                if only_x != None:
                    not_list.append((only_x, intersection))
        
        return(not_list)

    @staticmethod
    def count_effect(e_trues, windows) -> int:
        """
        Get the number of times where e is true in the provided time windows.

        Parameters:
            e_trues: the timepoints where e is true.
            windows: a list of windows, i.e. c_and_x and not_c_and_x.

        Returns:
            The number of times (Int) e was true in the provided time windows.
        """
        res = 0

        for (ws, we), intersection in windows:
            for e in e_trues:
                e_cases = e_trues[e]
                inter = [e_case for e_case in e_cases if e_case in intersection]
                if e >= ws and e <= we and len(inter) != 0:
                    res += 1
                    break
        
        return(res)

    @staticmethod
    def get_overlap(window1, window2) -> Tuple[float, float]:
        """
        Get the overlap of two time windows.
        """
        r, s = window1
        p, q = window2

        # (r, s) must always represent the first time window
        if p < r:
            r, s = window2
            p, q = window1
        
        # if window 1 ends before window 2 starts, then there is no overlap
        if s < p:
            return(None)
        else:
            return((p, s))

    @staticmethod
    def get_only_x(window_c, window_x) -> Tuple[float, float]:
        """
        Of the two time windows, return the period where only factor x is observed.
        """
        r, s = window_c
        p, q = window_x

        # if c happens before x, get the latter part starting when c ends
        if r < p:
            return((s, q))
        # when x starts first, get the first part until c starts
        elif p < r:
            return((p, r))
        # when both windows are the same, return None
        else:
            return(None)
