import logging
import queue  # Changed from 'Queue' to 'queue' in Python 3

from concurrent import futures
from progress.bar import Bar

from websocket_fuzzer.main.websocket_wrapper import send_payloads_in_websocket
from websocket_fuzzer.tokenizer import TOKEN
from websocket_fuzzer.tokenizer.tokenizer import create_tokenized_messages


PAYLOADS = 'websocket_fuzzer/payloads/payloads.txt'


class ThreadPoolExecutorWithQueueSizeLimit(futures.ThreadPoolExecutor):
    def __init__(self, maxsize=50, *args, **kwargs):
        super(ThreadPoolExecutorWithQueueSizeLimit, self).__init__(*args, **kwargs)
        self._work_queue = queue.Queue(maxsize=maxsize)  # Updated from Queue.Queue to queue.Queue


def fuzz_websockets(ws_address, init_messages, original_messages, session_active_message,
                    ignore_tokens, ignore_errors, output, http_proxy_host, http_proxy_port):
    """
    Creates a websocket connection, sends the payloads, writes output to disk.

    :param ws_address: The websocket address to connect and send messages to
    :param init_messages: The login messages to send before any payloads.
    :param session_active_message: Wait for this message after sending the init_messages. 
                                   This is usually the message that says: "Login successful". 
                                   Use None if there are no messages to wait for.
    :param original_messages: The original messages to be fuzzed.
    :param ignore_tokens: List of tokens in the message that should not be fuzzed.
    :param ignore_errors: List of errors to ignore during the fuzzing process.
    :param output: Path where the output should be saved.
    :param http_proxy_host: The HTTP host (None if proxy shouldn't be used).
    :param http_proxy_port: The HTTP proxy port (None if proxy shouldn't be used).
    :return: None
    """
    logging.info('Starting the fuzzing process...')
    
    # Use 'with open' for file handling in Python 3
    with open(PAYLOADS, 'r') as file:
        payload_count = len(file.readlines())

    with ThreadPoolExecutorWithQueueSizeLimit(max_workers=25) as ex:

        for original_message in original_messages:
            # Serialize message if it's a callable function
            original_message = serialize_message(original_message)

            logging.info(f'Fuzzing message: {original_message}')
            tokenized_messages = create_tokenized_messages(original_message, ignore_tokens)

            bar = Bar('Processing', max=len(tokenized_messages) * payload_count)

            for tokenized_count, tokenized_message in enumerate(tokenized_messages):
                with open(PAYLOADS, 'r') as file:
                    for payload in file:
                        bar.next()

                        # Modify the message by replacing the token with the payload
                        modified_message = replace_token_in_json(payload, tokenized_message)

                        logging.debug(f'Generated fuzzed message: {modified_message}')

                        messages_to_send = init_messages[:]
                        messages_to_send.append(modified_message)

                        # Submit fuzzing task to the thread pool executor
                        ex.submit(send_payloads_in_websocket,
                                  ws_address,
                                  messages_to_send,
                                  session_active_message,
                                  ignore_errors,
                                  tokenized_count,
                                  output,
                                  http_proxy_host,
                                  http_proxy_port)

            bar.finish()

    logging.debug('Finished fuzzing process')


def replace_token_in_json(payload, tokenized_message):
    """
    Replace the token in the tokenized message with the payload.
    :param payload: The payload to replace the token with.
    :param tokenized_message: The tokenized message that needs to be modified.
    :return: The modified message.
    """
    # Escape any quotes in the payload
    payload = payload.strip()
    payload = payload.replace('"', '\\"')

    # Replace the token with the payload in the tokenized message
    modified_message = tokenized_message.replace(TOKEN, payload)
    return modified_message


def serialize_message(message):
    """
    This method gives the fuzzer support for using functions as messages.
    The function will be called to generate the message.

    :param message: A string with the message, or a function that generates
                    the message to send to the wire.

    :return: A string with the message
    """
    if callable(message):
        return message()  # Call the function to get the message
    return message  # Return the message if it's a string
