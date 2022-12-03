import telebot
from telebot import types

bot = telebot.TeleBot('5643613529:AAEsBTAhiNXQBtoWTpoyl52HeF_4CFYjwRI')

ask_length = "Write heater length <b>(first)</b> and electric cable length <b>(second)</b> with space.\n" \
             "<b>Example:</b> 69 777  \n------------\n" \
             "Напиши <b>сначала</b> длину греющего кабеля, <b>затем</b> длину силового кабеля через пробел\n" \
             "<b>Example:</b> 69 777"



def calc_u_losses(info_dict, s_cable):
    resists = {
        '1.5': [12.3, 0],
        '2.5': [7.4, 0.104],
        '4': [4.13, 0.095],
        '6': [3.09, 0.09],
        '10': [1.84, 0.073],
        '16': [1.16, 0.068],
        '25': [0.74, 0.066],
    }
    r = resists.get(s_cable)
    real_r = r[0]
    reac_r = r[1]
    cable_l = float(info_dict.get('c_length'))
    i = float(info_dict.get('i_nom'))
    z = cable_l * (real_r / 1000 * 0.98 + reac_r / 1000 * 0.2)
    d_u = 100 * (3 ** 0.5) * i * z * 2 / 380
    return d_u


def calc(info_dict, info_length):
    h_length = info_length[0]  # get heater length
    c_length = info_length[1]  # get power cable length
    sum_nom_power = int(info_dict.get('nom_power')) * int(h_length)
    i_nom = sum_nom_power / 220 / 0.98  # nominal current
    global i_start
    global good_cb
    if info_dict.get("load_name") == "Constant Wattage Heating Cable":
        i_start = i_nom * 1.05  # startup current
    elif info_dict.get("load_name") == "Self-Regulating Heating Cable":
        i_start = i_nom * 2.3  # startup current
    # choosing cb
    c_breakers = [6, 10, 16, 20, 25, 32, 40]
    good_cb_list = []
    for cb in c_breakers:
        if i_start * 1.2 <= cb:
            good_cb_list.append(cb)
            break
        else:
            continue
    if len(good_cb_list) == 1:
        good_cb = str(good_cb_list[0])
        return info_dict.setdefault('h_length', h_length), \
               info_dict.setdefault('c_length', c_length), \
               info_dict.setdefault('good_cb', good_cb), \
               info_dict.setdefault('sum_nom_power', sum_nom_power), \
               info_dict.setdefault('i_nom', "{0:.1f}".format(i_nom)), \
               info_dict.setdefault('i_start', "{0:.1f}".format(i_start))
    else:
        return info_dict.setdefault('good_cb', 'Circuit breaker is not found')


def choose_power_cable(info_dict):
    goodcb = info_dict.get('good_cb')
    cables = {                           # the dict for relation CB and current
        '6': [1.5, 2.5, 4, 6, 10, 16, 25],
        '10': [1.5, 2.5, 4, 6, 10, 16, 25],
        '16': [2.5, 4, 6, 10, 16, 25],
        '20': [2.5, 4, 6, 10, 16, 25],
        '25': [4, 6, 10, 16, 25],
        '32': [4, 6, 10, 16, 25],
        '40': [6, 10, 16, 25],
    }
    good_s_cable_list = []
    for s_cable in cables.get(goodcb): # take first cb
        if calc_u_losses(info_dict, str(s_cable)) <= 3.5:
            good_s_cable_list.append(s_cable)
            break
        else:
            continue
    if len(good_s_cable_list) == 1:
        good_s_cable = str(good_s_cable_list[0])
        return info_dict.setdefault('good_s_cable', good_s_cable)
    else:
        return info_dict.setdefault('good_s_cable', 'Power cable is not found')




# Start of bot
@bot.message_handler(commands=['start'])
def start(message):
    info_dict.clear()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Constant Wattage Heating Cable")
    btn2 = types.KeyboardButton("Self-Regulating Heating Cable")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f'Hi, <b>{message.from_user.first_name}</b>! The bot helps you to select a power '
                                      f'cables and a circuit breaker for power supply of your electrical heating cable.'
                                      f'\n\n'
                                      f'<b>Choose type of heater:</b>\n'
                                      f'\n------------\n'
                                      f'Привет, <b>{message.from_user.first_name}</b>! Этот бот помогает подобрать '
                                      f'силовой кабель и автоматический выключатель для подключения греющего кабеля.\n\n'
                                      f'<b>Constant Wattage Heating Cable</b> - резистивный кабель\n'
                                      f'<b>Self-Regulating Heating Cable</b> - саморегулирующийся кабель\n\n'
                                      f'<b>Выберите тип кабеля:</b>',
                     parse_mode='html', reply_markup=markup)  # write a start message


info_dict = {}


@bot.message_handler(content_types=['text'])
def func(message):
    # Step 2  - choose type of cable
    if message.text == "Constant Wattage Heating Cable":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("16 W/m")
        btn2 = types.KeyboardButton("20 W/m")
        btn3 = types.KeyboardButton("24 W/m")
        btn4 = types.KeyboardButton("28 W/m")
        btn5 = types.KeyboardButton("30 W/m")
        back = types.KeyboardButton("Back / Назад")
        markup.add(btn1, btn2, btn3, btn4, btn5, back)
        bot.send_message(message.chat.id, text=f'Choose nominal power output (W/m)'
                                               f'\n------------\n'
                                               f'Выберите номинальную (погонную) мощность кабеля'
                         , parse_mode='html', reply_markup=markup)
        return info_dict.setdefault('load_name', "Constant Wattage Heating Cable")
    elif message.text == "Self-Regulating Heating Cable":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("16 W/m")
        btn2 = types.KeyboardButton("20 W/m")
        btn3 = types.KeyboardButton("24 W/m")
        btn4 = types.KeyboardButton("28 W/m")
        btn5 = types.KeyboardButton("30 W/m")
        back = types.KeyboardButton("Back / Назад")
        markup.add(btn1, btn2, btn3, btn4, btn5, back)
        bot.send_message(message.chat.id, text=f'Choose nominal power output (W/m)'
                                               f'\n------------\n'
                                               f'Выберите номинальную (погонную) мощность кабеля (Вт/м)'
                         , parse_mode='html', reply_markup=markup)
        return info_dict.setdefault('load_name', "Self-Regulating Heating Cable")

    # Step 3 - choose nom power
    elif message.text == "16 W/m":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Back / Назад")
        strt = types.KeyboardButton("Start over / С начала")
        markup.add(back, strt)
        bot.send_message(message.chat.id, text=ask_length, parse_mode='html', reply_markup=markup)
        return info_dict.setdefault('nom_power', '16')
    elif message.text == "20 W/m":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Back / Назад")
        strt = types.KeyboardButton("Start over / С начала")
        markup.add(back, strt)
        bot.send_message(message.chat.id, text=ask_length, parse_mode='html', reply_markup=markup)
        return info_dict.setdefault('nom_power', '20')
    elif message.text == "24 W/m":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Back / Назад")
        strt = types.KeyboardButton("Start over / С начала")
        markup.add(back, strt)
        bot.send_message(message.chat.id, text=ask_length, parse_mode='html', reply_markup=markup)
        return info_dict.setdefault('nom_power', '24')
    elif message.text == "28 W/m":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Back / Назад")
        strt = types.KeyboardButton("Start over / С начала")
        markup.add(back, strt)
        bot.send_message(message.chat.id, text=ask_length, parse_mode='html', reply_markup=markup)
        return info_dict.setdefault('nom_power', '28')
    elif message.text == "30 W/m":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Back / Назад")
        strt = types.KeyboardButton("Start over / С начала")
        markup.add(back, strt)
        bot.send_message(message.chat.id, text=ask_length, parse_mode='html', reply_markup=markup)
        return info_dict.setdefault('nom_power', '30')

    # start over option
    elif message.text == "Start over / С начала":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Constant Wattage Heating Cable")
        btn2 = types.KeyboardButton("Self-Regulating Heating Cable")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id,
                         f'Hi, <b>{message.from_user.first_name}</b>! The bot helps you to select a power '
                         f'cables and a circuit breaker for power supply of your electrical heating cable.'
                         f'\n\n'
                         f'<b>Choose type of heater:</b>\n'
                         f'\n------------\n'
                         f'Привет, <b>{message.from_user.first_name}</b>! Этот бот помогает подобрать '
                         f'силовой кабель и автоматический выключатель для подключения греющего кабеля.\n\n'
                         f'<b>Constant Wattage Heating Cable</b> - резистивный кабель\n'
                         f'<b>Self-Regulating Heating Cable</b> - саморегулирующийся кабель\n\n'
                         f'<b>Выберите тип кабеля:</b>',
                         parse_mode='html', reply_markup=markup)  # write a start message
        return info_dict.clear()


    # back option
    elif message.text == "Back / Назад":
        # работает при нажатии back во время выбора номинальной мощности (все начинается с начала)
        if info_dict.get('nom_power') == None:
            info_dict.clear()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Constant Wattage Heating Cable")
            btn2 = types.KeyboardButton("Self-Regulating Heating Cable")
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id,
                             f'Hi, <b>{message.from_user.first_name}</b>! The bot helps you to select a power '
                             f'cables and a circuit breaker for power supply of your electrical heating cable.'
                             f'\n\n'
                             f'<b>Choose type of heater:</b>\n'
                             f'\n------------\n'
                             f'Привет, <b>{message.from_user.first_name}</b>! Этот бот помогает подобрать '
                             f'силовой кабель и автоматический выключатель для подключения греющего кабеля.\n\n'
                             f'<b>Constant Wattage Heating Cable</b> - резистивный кабель\n'
                             f'<b>Self-Regulating Heating Cable</b> - саморегулирующийся кабель\n\n'
                             f'<b>Выберите тип кабеля:</b>',
                             parse_mode='html', reply_markup=markup)  # write a start message
            return info_dict.clear()
        # работает при нажатии back при НЕвыборе автомата защиты
        elif info_dict.get('good_cb') == 'Circuit breaker is not found':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton("Back / Назад")
            strt = types.KeyboardButton("Start over / С начала")
            markup.add(back, strt)
            bot.send_message(message.chat.id, text=f'{ask_length}', parse_mode='html', reply_markup=markup)
            return info_dict.pop('good_cb')
        # работает при нажатии back во время ввода длин кабелей (возвращает на момент выбора мощности)
        elif info_dict.get("h_length") == None or info_dict.get("c_length") == None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("16 W/m")
            btn2 = types.KeyboardButton("20 W/m")
            btn3 = types.KeyboardButton("24 W/m")
            btn4 = types.KeyboardButton("28 W/m")
            btn5 = types.KeyboardButton("30 W/m")
            back = types.KeyboardButton("Back / Назад")
            markup.add(btn1, btn2, btn3, btn4, btn5, back)
            bot.send_message(message.chat.id, text=f'Choose nominal power output (W/m)'
                                                   f'\n------------\n'
                                                   f'Выберите номинальную (погонную) мощность кабеля (Вт/м)'
                             , parse_mode='html', reply_markup=markup)
            return info_dict.pop('nom_power')
        # работает при нажатии back в моменте кабель неподобран или подобран а юзер хочет заново подобрать кабель
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton("Back / Назад")
            strt = types.KeyboardButton("Start over / С начала")
            markup.add(back, strt)
            bot.send_message(message.chat.id, text=f'{ask_length}', parse_mode='html', reply_markup=markup)
            return info_dict.pop('h_length'), \
                   info_dict.pop('good_s_cable'), \
                   info_dict.pop('c_length'), \
                   info_dict.pop('good_cb'), \
                   info_dict.pop('sum_nom_power'), \
                   info_dict.pop('i_nom'), \
                   info_dict.pop('i_start')

    # Step 4 - work with lengths
    elif type(message.text) == str:
        info_length = message.text.split()
        # Check 1 - find stupid message almost in any moment
        if info_dict.get('load_name') == None or info_dict.get('nom_power') == None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Constant Wattage Heating Cable")
            btn2 = types.KeyboardButton("Self-Regulating Heating Cable")
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id,
                             f'Hi, <b>{message.from_user.first_name}</b>! The bot helps you to select a power '
                             f'cables and a circuit breaker for power supply of your electrical heating cable.'
                             f'\n\n'
                             f'<b>Choose type of heater:</b>\n'
                             f'\n------------\n'
                             f'Привет, <b>{message.from_user.first_name}</b>! Этот бот помогает подобрать '
                             f'силовой кабель и автоматический выключатель для подключения греющего кабеля.\n\n'
                             f'<b>Constant Wattage Heating Cable</b> - резистивный кабель\n'
                             f'<b>Self-Regulating Heating Cable</b> - саморегулирующийся кабель\n\n'
                             f'<b>Выберите тип кабеля:</b>',
                             parse_mode='html', reply_markup=markup)  # write a start message
            return info_dict.clear()
        # Check 2 - find stupid message in the moment when person need to write length of heater
        try:
            float(info_length[0])
        except:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton("Back / Назад")
            strt = types.KeyboardButton("Start over / С начала")
            markup.add(back, strt)
            return bot.send_message(message.chat.id,
                             text=f'<b>WARNING! Wrong content. Try again</b>'
                                  f'\n------------\n'
                                  f'<b>ВНИМАНИЕ! Неправильное значение. Введите еще раз</b>\n\n{ask_length}',
                                    parse_mode='html', reply_markup=markup
                             )
        # Check 3 - find stupid message in the moment when person need to write length of power cable
        try:
            float(info_length[1])
        except:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton("Back / Назад")
            strt = types.KeyboardButton("Start over / С начала")
            markup.add(back, strt)
            return bot.send_message(message.chat.id,
                             text=f'<b>WARNING! Wrong content. Try again</b>'
                                  f'\n------------\n'
                                  f'<b>ВНИМАНИЕ! Неправильное значение. Введите еще раз</b>\n\n{ask_length}',
                                    parse_mode='html', reply_markup=markup
                             )
        # Check 4 - check that user write 2 numbers
        if len(info_length) == 2:
            calc(info_dict, info_length)
            if info_dict.get('good_cb') == 'Circuit breaker is not found':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                back = types.KeyboardButton("Back / Назад")
                strt = types.KeyboardButton("Start over / С начала")
                markup.add(back, strt)
                bot.send_message(message.chat.id,
                                 text='Circuit breaker is not found. Load is too much. \n<b>We recommend to divide this'
                                      'heating cable into 2 sections and use 2 feeders for their power supply</b> '
                                      '\n------------\n'
                                      '<b>Автоматический выключатель не подобран. Нагрузка слишком большая. Мы рекомендуем '
                                      'разделить гр.кабель на 2 секции и использовать 2 фидера для их подключения.</b>',
                                 parse_mode='html', reply_markup=markup
                                 )
            else:
                choose_power_cable(info_dict)
                if info_dict.get('good_s_cable') == 'Power cable is not found':
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    back = types.KeyboardButton("Back / Назад")
                    strt = types.KeyboardButton("Start over / С начала")
                    markup.add(back, strt)
                    bot.send_message(message.chat.id,
                                     text='Power cable is not found. Voltage loss is too much. \n'
                                          '<b>We recommend to divide this'
                                          'heating cable into 2 sections and use 2 feeders for their power supply</b> '
                                          '\n------------\n'
                                          '<b>Силовой кабель не подобран. Потеря напряжения слишком большая. Мы рекомендуем '
                                          'разделить гр.кабель на 2 секции и использовать 2 фидера для их подключения.</b>',
                                     parse_mode='html', reply_markup=markup
                                     )
                else:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    back = types.KeyboardButton("Back / Назад")
                    strt = types.KeyboardButton("Start over / С начала")
                    markup.add(back, strt)
                    bot.send_message(message.chat.id,
                                     text=f'Nominal power of {info_dict.get("load_name")} = {info_dict.get("nom_power")} W/m.\n'
                                          f'Total power = {info_dict.get("sum_nom_power")} W\n'
                                          f'Heater length = {info_dict.get("h_length")} meters\n'
                                          f'Power cable length = {info_dict.get("c_length")} meters\n'
                                          f'Nominal current = {info_dict.get("i_nom")} A\n'
                                          f'Startup current = {info_dict.get("i_start")} A\n'
                                          f'<b>Circuit Breaker = {info_dict.get("good_cb")}A</b>\n'
                                          f'<b>Power cable = ВВГнгLS(A)-3x{info_dict.get("good_s_cable")}</b>',
                                     parse_mode='html', reply_markup=markup
                                     )
                    if info_dict.get('good_cb') == '40':
                        bot.send_message(message.chat.id,
                                         text="WARNING! Circuit breaker is 40A. Check maximum current for the heater."
                                              "Use the CB if maximum current of the heater is more 40A.\n\n"
                                              "<b>We don't recommend using the CB, when maximum current of the heater = 40A</b>\n\n"
                                              "We recommend to divide this heating cable into 2 sections and use 2 feeders for "
                                              "their power supply"
                                              "\n_________\n"
                                              "ВНИМАНИЕ! Автомат.выключатель 40А. Проверьте максимальный ток греющего кабеля."
                                              " Используй данный автомат, если максимальный ток гр.кабеля больше 40А.\n\n"
                                              "<b>Мы не рекомендуем использовать данный автомат, если максимальный ток "
                                              "гр.кабеля равен 40А</b>\n\nМы рекомендуем разделить гр.кабель на 2 секции и "
                                              "использовать 2 фидера для их подключения.", parse_mode='html'
                                         )
                    elif info_dict.get('good_cb') == '32':
                        bot.send_message(message.chat.id,
                                         text="WARNING! Circuit breaker is 32A. Check maximum current for the heater."
                                              "Use the CB if maximum current of the heater is more 32A.\n\n"
                                              "<b>We don't recommend using the CB, when maximum current of the heater = 32A</b>\n\n"
                                              "We recommend to divide this heating cable into 2 sections and use 2 feeders for "
                                              "their power supply"
                                              "\n_________\n"
                                              "ВНИМАНИЕ! Автомат.выключатель 32А. Проверьте максимальный ток греющего кабеля."
                                              " Используй данный автомат, если максимальный ток гр.кабеля больше 32А.\n\n"
                                              "<b>Мы не рекомендуем использовать данный автомат, если максимальный ток "
                                              "гр.кабеля равен 32А</b>\n\nМы рекомендуем разделить гр.кабель на 2 секции и "
                                              "использовать 2 фидера для их подключения.", parse_mode='html'
                                         )
                    elif info_dict.get('good_s_cable') == '1.5':
                        bot.send_message(message.chat.id,
                                         text="WARNING! Size of power cable is 1.5 mm2.\n\n"
                                              "<b>You better choose 2.5 mm2 size for reserve</b>"
                                              "\n_________\n\n"
                                              "ВНИМАНИЕ! Сечение кабеля - 1.5мм2.\n\n"
                                              "<b>Лучше выбрать кабель с сечением 2.5 мм2, чтобы предусмотреть запас</b>\n\n"
                                              , parse_mode='html'
                                         )
        # else:
        #     bot.send_message(message.chat.id,
        #                      text="WARNING! Wrong content. Try again"
        #                      )
        # return info_dict.clear()


bot.polling(none_stop=True)

