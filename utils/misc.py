def first_occurrence_index(l, val, after_index=None):
    """
    Find the first occurrence of some value, after_index will
    not be included in the possible return value
    
    :param l: 
    :param val: value to look for
    :param after_index: exclusive beginning of the range
    :return: zero-based index
    """
    if after_index is None:
        after_index = -1
    return after_index + 1 + l[after_index+1:].index(val)


def last_occurrence_index(l, val, before_index=None):
    """
    Find the last occurrence of some value, before_index will
    not be included in the possible return value
    
    :param l: 
    :param val: value to look for
    :param before_index: exclusive ending of the range
    :return: zero-based index
    """
    if before_index is None:
        before_index = len(l)
    # find first occurrence in reverse
    return len(l[:before_index]) - 1 - \
           (l[:before_index])[::-1].index(val)
