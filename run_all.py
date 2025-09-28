'''# run_all.py
from master_sheet_updater import append_new_orders_to_master
from splitter import split_new_master_rows_chunks
from whatsapp_sender import send_new_personal_rows_via_whatsapp

def main():
    added = append_new_orders_to_master()
    if added > 0:
        split_new_master_rows_chunks(

            
        )
        send_new_personal_rows_via_whatsapp()
    else:
        print("Nothing new; skipping split and WhatsApp.")

if __name__ == "__main__":
    main()
'''
# run_all.py
from master_sheet_updater import append_new_orders_to_master
from splitter import split_new_master_rows_chunks
from manual_splitter import manual_split_loop
from whatsapp_sender import send_new_personal_rows_via_whatsapp

def main():
    added = append_new_orders_to_master()
    if added > 0:
        print("Choose distribution mode:")
        print("1. Auto Split (equal chunks)")
        print("2. Manual Split (you pick row ranges & agents)")
        mode = input("Enter 1 or 2: ").strip()

        if mode == "1":
            split_new_master_rows_chunks()
        elif mode == "2":
            manual_split_loop()
        else:
            print("❌ Invalid choice, skipping distribution.")
            return

        send_new_personal_rows_via_whatsapp()
    else:
        print("Nothing new; skipping split and WhatsApp.")

if __name__ == "__main__":
    main()
