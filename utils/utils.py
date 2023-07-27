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

# Splits the provided topic string into its parts and
# removes the specified number of leading parts
def split_and_strip_topic_to_list(topic, num_prefixes=0):
    return topic.split('.')[num_prefixes:]


def convert_val_between_ranges(in_val, in_range, out_range):
    ratio = in_val / (in_range[1] - in_range[0])
    scaled_out = ((out_range[1] - out_range[0]) * ratio) + out_range[0]
    return int(scaled_out)

def replace_invalid_characters(topic):
    out = topic.replace('+', 'REPL_PLUS')
    out = out.replace('-', 'REPL_MINUS')
    return out

def restore_invalid_characters(topic):
    out = topic.replace('REPL_PLUS', '+')
    out = out.replace('REPL_MINUS', '-')
    return out
