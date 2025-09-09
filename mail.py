def get_code(username: str, password: str, imap_url) -> str:
    import imaplib
    import email
    from email.header import decode_header
    import re
    from os import path
    
    imap = imaplib.IMAP4_SSL(imap_url) # Выбор IMAP сервера

    imap.login(username, password) # Логин через выбранный IMAP сервер

    imap.select("MICROSOFT") # Выбор папки писем

    status, response = imap.search(None, "ALL") # Получение всех писем из папки писем

    msg_ids = response[0].split() # Разделение ID писем в list
    msg_id = msg_ids[-1] # Выбор последнего письма
    status, msg = imap.fetch(msg_id, "(RFC822)") # Получение содержания последнего письма
    msg = email.message_from_bytes(msg[0][1]) # Сборка письма в кортеж
    
    try: # Если заголовок письма на русском языке
        subject_letter = decode_header(msg["Subject"])[0][0].decode("utf-8").strip().replace("\xa0", " ")
    except AttributeError: subject_letter = msg["Subject"] # Если заголовок письма на латинице
    if subject_letter in ["Your single-use code", "Microsoft account security code", "Код безопасности для учетной записи Майкрософт"]: # Если заголовок письма такой, то
        for part in msg.walk():
            if part.get_content_type() == "text/plain":  # Текстовая часть
                payload = part.get_payload(decode=True)
                body = payload.decode("utf-8")
                body_str = re.split("\n| |\r", body)
                for element in body_str:
                    if len(element) == 6:
                        try:
                            new_code = element

                            if not path.exists("last_code.txt") or new_code != open("last_code.txt").readline().strip():
                                with open("last_code.txt", "w") as f:
                                    f.write(str(new_code))
                                return new_code
                            else:
                                return None
                        except ValueError:
                            continue
    imap.logout()