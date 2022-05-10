def gen_sql_in_tup(num_vals):
    if num_vals == 0:
        return "(FALSE)"
    return "(" + ",".join(["%s"] * num_vals) + ")"