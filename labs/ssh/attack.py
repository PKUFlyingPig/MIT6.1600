import zlib

class AttackTamper:
    def __init__(self, compress):
        # compress is set for the last extra credit part
        self.compress = compress
        self.bytes = 0
        self.t = 0

    def handle_data(self, data):
        # Your attack here.
        self.t += 1
        if self.t == 10:
            plain_text = "ls ./files/*".encode('utf-8')
            if self.compress:
                compressed_plain_text = zlib.compress(plain_text)
                target_text = "  rm -r /                                         ".encode('utf-8')
                compressed_target_text = zlib.compress(target_text)
                print(len(plain_text))
                assert len(compressed_plain_text) == len(compressed_target_text)
                payload_len = len(compressed_plain_text)
                altered_data = bytes([data[i + 14] ^ compressed_plain_text[i] ^ compressed_target_text[i] for i in range(payload_len)])
                evil_data = data[:14] + altered_data + data[14+payload_len:]
            else:
                target_text = "rm -r /     ".encode('utf-8')
                altered_data = bytes([data[i + 14] ^ plain_text[i] ^ target_text[i] for i in range(12)])
                evil_data = data[:14] + altered_data + data[14+12:]
            return evil_data
        
        return data

def attack_decrypt(client_fn):
    all_countries = ['Sukhumi, Abkhazia', 'Kabul, Afghanistan', 'Episkopi Cantonment, Akrotiri and Dhekelia', 'Tirana, Albania', 'Algiers, Algeria', 'Pago Pago, American Samoa', 'Andorra la Vella, Andorra', 'Luanda, Angola', 'The Valley, Anguilla', "St. John's, Antigua and Barbuda", 'Buenos Aires, Argentina', 'Yerevan, Armenia', 'Oranjestad, Aruba', 'Georgetown, Ascension Island', 'Canberra, Australia', 'Vienna, Austria', 'Baku, Azerbaijan', 'Nassau, Bahamas', 'Manama, Bahrain', 'Dhaka, Bangladesh', 'Bridgetown, Barbados', 'Minsk, Belarus', 'Brussels, Belgium', 'Belmopan, Belize', 'Porto-Novo, Benin', 'Hamilton, Bermuda', 'Thimphu, Bhutan', 'Sucre, Bolivia', 'La Paz, Bolivia', 'Sarajevo, Bosnia and Herzegovina', 'Gaborone, Botswana', 'Brasília, Brazil', 'Road Town, British Virgin Islands', 'Bandar Seri Begawan, Brunei', 'Sofia, Bulgaria', 'Ouagadougou, Burkina Faso', 'Bujumbura, Burundi', 'Phnom Penh, Cambodia', 'Yaoundé, Cameroon', 'Ottawa, Canada', 'Praia, Cape Verde', 'George Town, Cayman Islands', 'Bangui, Central African Republic', "N'Djamena, Chad", 'Santiago, Chile', 'Beijing, China', 'Flying Fish Cove, Christmas Island', 'West Island, Cocos (Keeling) Islands', 'Bogotá, Colombia', 'Moroni, Comoros', 'Avarua, Cook Islands', 'San José, Costa Rica', 'Zagreb, Croatia', 'Havana, Cuba', 'Willemstad, Curaçao', 'Nicosia, Cyprus', 'Prague, Czech Republic', "Yamoussoukro, Côte d'Ivoire", 'Kinshasa, Democratic Republic of the Congo', 'Copenhagen, Denmark', 'Djibouti, Djibouti', 'Roseau, Dominica', 'Santo Domingo, Dominican Republic', 'Dili, East Timor (Timor-Leste)', 'Hanga Roa, Easter Island', 'Quito, Ecuador', 'Cairo, Egypt', 'San Salvador, El Salvador', 'Malabo, Equatorial Guinea', 'Asmara, Eritrea', 'Tallinn, Estonia', 'Addis Ababa, Ethiopia', 'Stanley, Falkland Islands', 'Tórshavn, Faroe Islands', 'Palikir, Federated States of Micronesia', 'Suva, Fiji', 'Helsinki, Finland', 'Paris, France', 'Cayenne, French Guiana', 'Papeete, French Polynesia', 'Libreville, Gabon', 'Banjul, Gambia', 'Tbilisi, Georgia', 'Berlin, Germany', 'Accra, Ghana', 'Gibraltar, Gibraltar', 'Athens, Greece', 'Nuuk, Greenland', "St. George's, Grenada", 'Hagåtña, Guam', 'Guatemala City, Guatemala', 'St. Peter Port, Guernsey', 'Conakry, Guinea', 'Bissau, Guinea-Bissau', 'Georgetown, Guyana', 'Port-au-Prince, Haiti', 'Tegucigalpa, Honduras', 'Budapest, Hungary', 'Reykjavík, Iceland', 'New Delhi, India', 'Jakarta, Indonesia', 'Tehran, Iran', 'Baghdad, Iraq', 'Dublin, Ireland', 'Douglas, Isle of Man', 'Jerusalem, Israel', 'Rome, Italy', 'Kingston, Jamaica', 'Tokyo, Japan', 'St. Helier, Jersey', 'Amman, Jordan', 'Astana, Kazakhstan', 'Nairobi, Kenya', 'Tarawa, Kiribati', 'Pristina, Kosovo', 'Kuwait City, Kuwait', 'Bishkek, Kyrgyzstan', 'Vientiane, Laos', 'Riga, Latvia', 'Beirut, Lebanon', 'Maseru, Lesotho', 'Monrovia, Liberia', 'Tripoli, Libya', 'Vaduz, Liechtenstein', 'Vilnius, Lithuania', 'Luxembourg, Luxembourg', 'Skopje, Macedonia', 'Antananarivo, Madagascar', 'Lilongwe, Malawi', 'Kuala Lumpur, Malaysia', 'Malé, Maldives', 'Bamako, Mali', 'Valletta, Malta', 'Majuro, Marshall Islands', 'Nouakchott, Mauritania', 'Port Louis, Mauritius', 'Mexico City, Mexico', 'Chisinau, Moldova', 'Monaco, Monaco', 'Ulaanbaatar, Mongolia', 'Podgorica, Montenegro', 'Plymouth, Montserrat', 'Rabat, Morocco', 'Maputo, Mozambique', 'Naypyidaw, Myanmar', 'Stepanakert, Nagorno-Karabakh Republic', 'Windhoek, Namibia', 'Yaren, Nauru', 'Kathmandu, Nepal', 'Amsterdam, Netherlands', 'Nouméa, New Caledonia', 'Wellington, New Zealand', 'Managua, Nicaragua', 'Niamey, Niger', 'Abuja, Nigeria', 'Alofi, Niue', 'Kingston, Norfolk Island', 'Pyongyang, North Korea', 'Nicosia, Northern Cyprus', 'Belfast, United Kingdom Northern Ireland', 'Saipan, Northern Mariana Islands', 'Oslo, Norway', 'Muscat, Oman', 'Islamabad, Pakistan', 'Ngerulmud, Palau', 'Jerusalem, Palestine', 'Panama City, Panama', 'Port Moresby, Papua New Guinea', 'Asunción, Paraguay', 'Lima, Peru', 'Manila, Philippines', 'Adamstown, Pitcairn Islands', 'Warsaw, Poland', 'Lisbon, Portugal', 'San Juan, Puerto Rico', 'Doha, Qatar', 'Taipei, Republic of China (Taiwan)', 'Brazzaville, Republic of the Congo', 'Bucharest, Romania', 'Moscow, Russia', 'Kigali, Rwanda', 'Gustavia, Saint Barthélemy', 'Jamestown, Saint Helena', 'Basseterre, Saint Kitts and Nevis', 'Castries, Saint Lucia', 'Marigot, Saint Martin', 'St. Pierre, Saint Pierre and Miquelon', 'Kingstown, Saint Vincent and the Grenadines', 'Apia, Samoa', 'San Marino, San Marino', 'Riyadh, Saudi Arabia', 'Edinburgh, Scotland', 'Dakar, Senegal', 'Belgrade, Serbia', 'Victoria, Seychelles', 'Freetown, Sierra Leone', 'Singapore, Singapore', 'Philipsburg, Sint Maarten', 'Bratislava, Slovakia', 'Ljubljana, Slovenia', 'Honiara, Solomon Islands', 'Mogadishu, Somalia', 'Hargeisa, Somaliland', 'Pretoria, South Africa', 'Grytviken, South Georgia and the South Sandwich Islands', 'Seoul, South Korea', 'Tskhinvali, South Ossetia', 'Juba, South Sudan', 'Madrid, Spain', 'Sri Jayawardenapura Kotte, Sri Lanka', 'Khartoum, Sudan', 'Paramaribo, Suriname', 'Mbabane, Swaziland', 'Stockholm, Sweden', 'Bern, Switzerland', 'Damascus, Syria', 'São Tomé, São Tomé and Príncipe', 'Dushanbe, Tajikistan', 'Dodoma, Tanzania', 'Bangkok, Thailand', 'Lomé, Togo', 'Nukuʻalofa, Tonga', 'Tiraspol, Transnistria', 'Port of Spain, Trinidad and Tobago', 'Edinburgh of the Seven Seas, Tristan da Cunha', 'Tunis, Tunisia', 'Ankara, Turkey', 'Ashgabat, Turkmenistan', 'Cockburn Town, Turks and Caicos Islands', 'Funafuti, Tuvalu', 'Kampala, Uganda', 'Kyiv, Ukraine', 'Abu Dhabi, United Arab Emirates', 'London, United Kingdom; England', 'Washington, D.C., United States', 'Charlotte Amalie, United States Virgin Islands', 'Montevideo, Uruguay', 'Tashkent, Uzbekistan', 'Port Vila, Vanuatu', 'Vatican City, Vatican City', 'Caracas, Venezuela', 'Hanoi, Vietnam', 'Cardiff, Wales', 'Mata-Utu, Wallis and Futuna', 'El Aaiún, Western Sahara', 'Sanaá, Yemen', 'Lusaka, Zambia', 'Harare, Zimbabwe']
    # Your attack here.
    prefix_candidates = ["{\n"]

    # three cities
    for i in range(3):
        best_score = float("inf")
        new_candidates = []

        for prefix_candidate in prefix_candidates:
            for c in all_countries:
                if c in prefix_candidate:
                    continue
                probe = prefix_candidate + '"city%d": "%s",\n' % (i, c)
                (bytes_out, bytes_in) = client_fn(probe)
                if bytes_out <= best_score:
                    if bytes_out < best_score:
                        new_candidates = []
                    best_score = bytes_out
                    new_candidates.append(probe)

        # print(new_candidates)
        prefix_candidates = new_candidates[:5]

    # for x in prefix_candidates:
    #     print(x)
    return prefix_candidates[0] + "}\n"

