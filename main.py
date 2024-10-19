# Tailwind-To-Css Converter by xKotelek @ https://kotelek.dev

import json, requests

classes_file = "./tailwind-classes.json"
tailwind_classes = json.load(open(classes_file, "r"))

def checksum_check():
    checksum_url = "https://github.com/xKotelek/tailwind-to-css/tailwind-classes.json"