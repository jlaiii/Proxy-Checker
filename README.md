# Proxy Checker

This is a Python script that allows you to check the validity of a list of proxies. It supports HTTP, SOCKS4, and SOCKS5 proxy types. The script uses Google's domain to test the proxies and saves the good ones in a file named "good_proxies.txt".

## Usage

1. Create a file named `proxies.txt` in the same folder as the script. Each line should contain a proxy in the format `IP:PORT`.

2. Run the script using the following command:

    ```
    python proxy_checker.py
    ```

3. The script will prompt you to select a proxy type: HTTP (1), SOCKS4 (2), or SOCKS5 (3). Enter the corresponding number.

4. The script will start checking the proxies and display the progress. It will save the working proxies in the file "good_proxies.txt".

5. Once all proxies have been checked, the script will display a message. Press Enter to exit the script.

## Requirements

- Python 3.x
- The `requests` library is required. You can install it using the following command:

    ```
    pip install requests
    ```

## Notes

- Use this script responsibly and only on websites where you have the right to test proxies.
- The timeout for checking each proxy is set to 5 seconds. You can adjust this value in the script if needed.
- Proxies that are not working will be displayed in the console as they are checked.
- Make sure to review the results in the "good_proxies.txt" file after running the script.

Feel free to modify and improve this script according to your needs.

