def sample_function(data, word):
    """Locates all the indices with the word END
    Loops thorugh all of indices in patient data and creates a list of all
    the indices with the word END in order to find each patient's data
    Parameters
    ----------
    data : list
        Patient data with every row from the original file as an index without
        \n
    Returns
    -------
    ends : list
        List of indices from the patient data list with the word END
    """
    ends = []
    for i, x in enumerate(data):
        if x == word:
            ends.append(i)
    return ends