import glob
import argparse
import json
import numpy as np
import sklearn.cluster
import distance

from websocket_fuzzer.analysis.response_analyzer import analyze_response

# Set of messages to ignore during analysis
IGNORE_MESSAGES = {'error',
                   'xml',
                   'sqlattempt1',
                   'sqlattempt2'}

def distance_len(s1, s2):
    return len(s1) - len(s2)

def extract_description_from_message(message):
    try:
        return json.loads(message)['description']
    except:
        return 'Invalid JSON message: %s' % message

def unique_responses(output_path):
    max_count = get_max_socket_message_count(output_path)
    listing = glob.glob(output_path + '*-%s.log' % max_count)

    messages = [open(filename).read() for filename in listing]  # Read files using open()
    messages = [extract_description_from_message(m) for m in messages]
    messages = set(list(messages))

    print('\nUnique websocket responses:\n')

    for description in messages:
        print(f' - "{description}"')

def cluster_similar_responses(output_path):
    max_count = get_max_socket_message_count(output_path)
    listing = glob.glob(output_path + '*-%s.log' % max_count)

    messages = [open(filename).read() for filename in listing]  # Read files using open()
    messages = [extract_description_from_message(m) for m in messages]
    messages = np.asarray(messages)

    print(f'\nClustering {len(messages)} responses...(this might take a while)\n')

    lev_similarity = -1 * np.array([[distance.levenshtein(m1, m2) for m1 in messages] for m2 in messages])

    affprop = sklearn.cluster.AffinityPropagation(affinity='precomputed', damping=0.5)
    affprop.fit(lev_similarity)

    print('\nGenerated clusters:\n')

    for cluster_id in np.unique(affprop.labels_):
        exemplar = messages[affprop.cluster_centers_indices_[cluster_id]]
        cluster = np.unique(messages[np.nonzero(affprop.labels_ == cluster_id)])
        cluster_str = ', '.join(cluster)
        print('-' * 80)
        print(f' - *{exemplar}:* {cluster_str}')
        print('-' * 80)
        print()

def analyze_responses_with_fingerprints(output_path):
    manual_analysis = []

    # This depends on how websocket_logfile.py saves the output
    for filename in glob.glob(output_path + '*.log'):
        if analyze_response(open(filename).read(), IGNORE_MESSAGES):
            manual_analysis.append(filename)

    if not manual_analysis:
        return

    print('\nThese files require manual analysis:\n')

    for filename in manual_analysis:
        print(f' - {filename}')

def get_max_socket_message_count(output_path):
    has_no_messages = 0
    max_has_no_messages = 10
    max_count = 0

    for count in range(100):  # Use range instead of xrange in Python 3

        # This depends on how websocket_logfile.py saves the output
        listing = glob.glob(output_path + '*-%s.log' % count)

        if not listing:
            has_no_messages += 1
            if has_no_messages >= max_has_no_messages:
                break
            continue

        max_count = count

    # -1 because the last message will always be /closed
    return max_count - 1

def analyze_websocket_message_count(output_path):
    print('\nMost common message count per connection:\n')

    counts = {}

    for count in range(100):  # Use range instead of xrange in Python 3

        # This depends on how websocket_logfile.py saves the output
        listing = glob.glob(output_path + '*-%s.log' % count)

        connection_ids = []

        for filename in listing:
            filename = filename.replace(output_path, '')
            connection_id = filename.replace(f'-%s.log' % count, '')

            all_connection_ids = {x for v in counts.values() for x in v}  # Use values() instead of itervalues()

            if connection_id not in all_connection_ids:
                connection_ids.append(connection_id)

        counts[count] = connection_ids

    for count in reversed(list(counts.keys())):
        listing = counts[count]

        if not listing:
            continue

        listing_str = ', '.join(listing)
        print(f'Found {len(listing)} connections that sent {count} messages: {listing_str}\n')

def analyze_output(output_path):
    analyze_responses_with_fingerprints(output_path)
    analyze_websocket_message_count(output_path)
    # cluster_similar_responses()  # You can uncomment this if needed
    unique_responses(output_path)

def main():
    parser = argparse.ArgumentParser(description='Analyze fuzzer output')

    parser.add_argument('-o', action='store', dest='output_path', required=True,
                        help='Path to the fuzzer output directory (e.g., "output/0/")')

    results = parser.parse_args()
    analyze_output(results.output_path)

if __name__ == '__main__':
    main()
