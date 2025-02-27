def scrape_stream_production():
    global ENVOY_TOKEN
    ENVOY_TOKEN = token_gen(ENVOY_TOKEN)
    while True:
        try:
            url = 'http://%s/production.json' % ENVOY_HOST
            headers = {"Authorization": "Bearer " + ENVOY_TOKEN}
            stream = requests.get(url, timeout=5, verify=False, headers=headers)

            if stream.status_code == 401:
                print(dt_string, 'Failed to authenticate, generating new token')
                ENVOY_TOKEN = token_gen(None)
                headers = {"Authorization": "Bearer " + ENVOY_TOKEN}
                stream = requests.get(url, timeout=5, verify=False, headers=headers)
            elif stream.status_code != 200:
                print(dt_string, 'Failed to connect to Envoy:', stream.status_code)
            else:
                if is_json_valid(stream.content):
                    json_response = stream.json()

                    # Default op None zetten
                    power_value = None

                    # Probeer eerst de consumption data te pakken
                    if "consumption" in json_response and len(json_response["consumption"]) > 0:
                        if "wNow" in json_response["consumption"][0]:
                            power_value = round(json_response["consumption"][0]["wNow"])
                    
                    # Als consumption niet werkt, gebruik production
                    if power_value is None:
                        print(dt_string, "Consumption data niet beschikbaar, overschakelen naar Production")
                        if "production" in json_response and len(json_response["production"]) > 0:
                            if "wNow" in json_response["production"][0]:
                                power_value = round(json_response["production"][0]["wNow"])

                    # Als er een geldige waarde is gevonden, publiceer het naar MQTT
                    if power_value is not None:
                        json_string_freeds = json.dumps(power_value)
                        client.publish(topic=MQTT_TOPIC_FREEDS, payload=json_string_freeds, qos=0)
                        if DEBUG: print(dt_string, 'FREEDS JSON published:', json_string_freeds)
                    else:
                        print(dt_string, "Geen geldige power waarde gevonden in zowel consumption als production.")

                    # Publiceer de volledige JSON zoals het origineel
                    json_string = json.dumps(json_response)
                    client.publish(topic=MQTT_TOPIC, payload=json_string, qos=0)

                    time.sleep(1)
                else:
                    print(dt_string, 'Invalid JSON Response:', stream.content)

        except requests.exceptions.RequestException as e:
            print(dt_string, 'Exception fetching stream data:', e)
