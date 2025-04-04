# auto-journal

Run:

```sh
./run.sh
```

## Setup (Pull iMessage Data and Clean Up)
Pull existing iMessage data on your mac using imessage-exporter:
```sh
imessage-exporter -f txt -o ~/Documents/autojournal/Assets/<current_date in MM_DD format> -s <current_date-1> -e <current_date> -a macOS
```

To create contacts:
```
cd Assets
python3 create_contacts.py
```
To create a single file with all conversations, all phone numbers and emails converted to named contacts:
```
python3 text_to_person_mapper.py
```

