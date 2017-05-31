from utils import last_occurrence_index, first_occurrence_index


def generate_multiprocessing_final_pass_ranges(frame_acceptance_ctype,
                                               frame_count,
                                               task_per_worker,
                                               worker_count,
                                               skip_window_both_end,
                                               ):
    final_pass_ranges = [
        (last_occurrence_index(frame_acceptance_ctype, True, (task_per_worker * i - skip_window_both_end)),
         first_occurrence_index(frame_acceptance_ctype, True, (task_per_worker * i + skip_window_both_end)))
        for i in range(1, worker_count)]

    final_pass_ranges.append(
        (0, first_occurrence_index(frame_acceptance_ctype,
                                   True, skip_window_both_end)+1)
    )
    final_pass_ranges.append(
        (last_occurrence_index(frame_acceptance_ctype, True,
                               frame_count - skip_window_both_end),
         frame_count)
    )

    return final_pass_ranges
