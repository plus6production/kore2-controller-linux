# Some utility functions that are globally useful

data_log_file = './usb_log.txt'

def print_to_file(*args):
    print(args, file=open(data_log_file, 'a'), sep=': ')

def print_if_debug(debug, *args):
    if debug:
        print(args)

# Utility func to convert one byte of flags to a list of bit indices
def get_bit_flag_indices(flags):
    indices = []
    for x in range(8):
        if flags & (1 << x):
            indices.append(x)
    return indices