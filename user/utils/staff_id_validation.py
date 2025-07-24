def staff_id_check(staff_id):
    """
    Check that staff_id is at least 3 characters long.
    """
    error_list = []
    
    if not staff_id:
        return ["This field is required."]
    if len(staff_id) < 3:
        error_list.append("Staff id must be at least 3 characters long.")
    if len(staff_id) > 20:
        error_list.append("Staff id must not be more than 20 characters.")
    return error_list