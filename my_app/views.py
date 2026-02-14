
from datetime import datetime, timezone
from django.db.models import  Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.templatetags.static import static
from django.middleware.csrf import get_token
from .models import UserProfile, ChatMessage, WorkSchedule
import json
from django.views.decorators.csrf import csrf_exempt
import requests


def get_safe_razryad(user):
        try:
            if not user or not user.razryad:
                return 0
            r_str = str(user.razryad).strip()
            if "/" in r_str:
                num, den = r_str.split("/")
                return float(num) / float(den)
            return float(r_str)
        except (ValueError, TypeError, ZeroDivisionError):
            return 0

    # 2. OYLIK MENYUSI
def salary_menu_view(request):
        user_login = request.session.get('user_login')
        if not user_login:
            return redirect('/')

        user = UserProfile.objects.filter(login=user_login).first()
        if not user: return redirect('/')

        current_razryad = get_safe_razryad(user)

        # Avtomatik yo'naltirish (Razryadga qarab)
        auto_url = "/Conculator/" if current_razryad >= (5 / 3) else "/Kankulyator_Auto/"

        html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Oylik Menyusi</title>
            <style>
                body {{ margin: 0; padding: 0; height: 100vh; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; background: #000; color: white; }}
                .main-bg {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("/static/image.jpg") center/cover; z-index: -1; }}
                .menu-box {{ background: rgba(255,255,255,0.07); padding: 40px 30px; border-radius: 30px; text-align: center; width: 350px; backdrop-filter: blur(25px); border: 1px solid rgba(255,255,255,0.15); }}
                h1 {{ color: #00f2ff; text-transform: uppercase; font-size: 20px; margin-bottom: 25px; letter-spacing: 1px; }}
                .nav-link {{ display: block; padding: 16px; margin: 12px 0; background: rgba(255,255,255,0.08); color: white; text-decoration: none; border-radius: 15px; font-weight: 600; border: 1px solid rgba(255,255,255,0.1); transition: 0.3s; }}
                .nav-link:hover {{ background: #00f2ff; color: #000; transform: translateY(-3px); }}
                .nav-manual {{ border-color: #ff9d00; color: #ff9d00; }}
                .nav-manual:hover {{ background: #ff9d00; color: #000; }}
            </style>
        </head>
        <body>
            <div class="main-bg"></div>
            <div class="menu-box">
                <h1>Oylik Menyusi</h1>
                <p style="font-size: 12px; color: #aaa;">Razryadingiz: {user.razryad}</p>
                <a href="{auto_url}" class="nav-link">Avtomatik Hisoblash</a>
                <a href="/Kankulyator/" class="nav-link nav-manual">Mukofotni Qo'lda Kiritish</a>
                <a href="/second/" style="color:#888; text-decoration:none; font-size:13px; display:block; margin-top:20px;">← Orqaga</a>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)

    # 3. MUKOFOTNI QO'LDA KIRITADIGAN KALKULYATOR (HAMMA UCHUN)
def salary_calc_manual_view(request):
        user_login = request.session.get('user_login')
        if not user_login: return redirect('/')

        # Formadan ma'lumotlarni olish
        salary = request.GET.get('salary')
        norma_soat = request.GET.get('norma_soat')
        ishlangan_soat = request.GET.get('ishlangan_soat')
        bonus_input = request.GET.get('bonus_percent', 0)  # MUKOFOT FOIZI
        t_s = request.GET.get('tungi_soat', 0)
        b_s = request.GET.get('bayram_soati', 0)

        res_html = ""
        if salary and norma_soat and ishlangan_soat:
            try:
                s, n, i = float(salary), float(norma_soat), float(ishlangan_soat)
                bp = float(bonus_input) / 100  # Foizni songa o'girish (masalan 40 -> 0.4)
                ts, bs = float(t_s or 0), float(b_s or 0)

                m = s / n
                asosiy = m * i
                tungi = ts * (m * 0.5)
                mukofot = asosiy * bp
                pitaniye = (490000 / n) * i
                bayram = bs * m

                brutto = asosiy + mukofot + tungi + pitaniye + bayram
                soliq = brutto * 0.131
                netto = brutto - soliq

                res_html = f"""
                <div style="background: rgba(255, 157, 0, 0.1); border: 1px solid #ff9d00; padding: 15px; border-radius: 20px; margin-bottom: 20px;">
                    <p>Brutto: {brutto:,.0f} | Soliq: -{soliq:,.0f}</p>
                    <h3 style="color:#ff9d00; text-align:center;">Netto: {netto:,.0f} so'm</h3>
                </div>"""
            except:
                res_html = "<p style='color:red'>Xato ma'lumot kiritildi!</p>"

        return render_calc_page(request, res_html, is_manual=True)

    # 4. AVTOMATIK KALKULYATORLAR (Sizda bor bo'lgan mantiq)
def salary_calc_high(request):
        return common_auto_logic(request, 0.20)

def salary_calc_low(request):
        return common_auto_logic(request, 0.40)

def common_auto_logic(request, rate):
        # Bu yerga yuqoridagi salary_calc_manual_view ga o'xshash mantiqni rate bilan qo'yasiz
        # ... (vaqtni tejash uchun umumiy renderga o'tamiz)
        return render_calc_page(request, "", rate)

    # 5. UMUMIY RENDER FUNKSIYASI (FON RASMI BILAN)
def render_calc_page(request, res_html, rate=0, is_manual=False):
        title = "Mukofotni kiriting" if is_manual else f"{int(rate * 100)}% Mukofot"
        bonus_field = f'<label>Mukofot foizi (%):</label><input type="number" name="bonus_percent" value="40" required>' if is_manual else ""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ margin: 0; padding: 0; min-height: 100vh; font-family: sans-serif; background: #000; display: flex; justify-content: center; align-items: center; color: white; }}
                .main-bg {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("/static/image.jpg") center/cover; z-index: -1; }}
                .box {{ background: rgba(255,255,255,0.05); backdrop-filter: blur(25px); padding: 30px; border-radius: 30px; width: 90%; max-width: 380px; border: 1px solid rgba(255,255,255,0.1); }}
                h2 {{ color: #00f2ff; text-align: center; margin-top: 0; }}
                input {{ width: 100%; padding: 12px; margin: 8px 0; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.05); color: #fff; box-sizing: border-box; }}
                button {{ width: 100%; padding: 15px; border-radius: 20px; border: none; background: #00f2ff; color: #000; font-weight: bold; cursor: pointer; margin-top: 15px; }}
                label {{ font-size: 12px; color: #aaa; margin-left: 5px; }}
            </style>
        </head>
        <body>
            <div class="main-bg"></div>
            <div class="box">
                <h2>{title}</h2>
                {res_html}
                <form method="GET">
                    <label>Shtat oyligi:</label><input type="number" name="salary" required>
                    <label>Norma soat:</label><input type="number" name="norma_soat" required>
                    <label>Ishlangan soat:</label><input type="number" name="ishlangan_soat" required>
                    {bonus_field}
                    <label>Tungi soat:</label><input type="number" name="tungi_soat" value="0">
                    <label>Bayram soati:</label><input type="number" name="bayram_soati" value="0">
                    <button type="submit">HISOBLASH</button>
                </form>
                <a href="/okladmenu/" style="color:#ccc; display:block; text-align:center; margin-top:15px; text-decoration:none; font-size:13px;">← Orqaga</a>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)

    # 3. KATTA RAZRYADLAR (20% MUKOFOT)
def salary_calc_view(request):
        return common_calculator_logic(request, bonus_rate=0.20, check_type="high")

    # 4. KICHIK RAZRYADLAR (40% MUKOFOT)
def salary_calc_view1(request):
        return common_calculator_logic(request, bonus_rate=0.40, check_type="low")

    # 5. UMUMIY HISOB-KITOB LOGIKASI (FON RASMI BILAN)
def common_calculator_logic(request, bonus_rate, check_type):
        user_login = request.session.get('user_login')
        if not user_login:
            return redirect('/')

        user = UserProfile.objects.filter(login=user_login).first()
        current_razryad = get_safe_razryad(user)

        # Ruxsatni tekshirish
        limit = 5 / 3
        if check_type == "high" and current_razryad < limit:
            return HttpResponse("<h3>Xato: Ushbu bo'lim faqat yuqori razryadlar uchun!</h3>")
        if check_type == "low" and current_razryad >= limit:
            return HttpResponse("<h3>Xato: Ushbu bo'lim faqat kichik razryadlar uchun!</h3>")

        # Formadan ma'lumot olish
        salary = request.GET.get('salary')
        norma_soat = request.GET.get('norma_soat')
        ishlangan_soat = request.GET.get('ishlangan_soat')
        tungi_soat = request.GET.get('tungi_soat', 0)
        bayram_soati = request.GET.get('bayram_soati', 0)

        res_html = ""
        if salary and norma_soat and ishlangan_soat:
            try:
                s, n_s, i_s = float(salary), float(norma_soat), float(ishlangan_soat)
                t_s = float(tungi_soat) if tungi_soat else 0
                b_s = float(bayram_soati) if bayram_soati else 0

                m = s / n_s
                asosiy = m * i_s
                tungi_bonus = t_s * (m * 0.5)
                mukofot = asosiy * bonus_rate
                pitaniye = (490000 / n_s) * i_s
                bayram = b_s * m

                brutto = asosiy + mukofot + tungi_bonus + pitaniye + bayram
                soliqlar = brutto * (0.12 + 0.01 + 0.001)
                netto = brutto - soliqlar

                res_html = f"""
                <div style="background: rgba(0, 242, 255, 0.1); border: 1px solid #00f2ff; padding: 20px; border-radius: 20px; margin-bottom: 25px; text-align: left;">
                    <h3 style="color: #00f2ff; margin-top: 0; text-align: center;">Natija ({int(bonus_rate * 100)}% mukofot)</h3>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>Brutto:</span> <b>{brutto:,.0f} so'm</b>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>Soliq:</span> <b style="color: #ff4747;">-{soliqlar:,.0f} so'm</b>
                    </div>
                    <hr style="border: 0.5px solid rgba(255,255,255,0.1);">
                    <div style="text-align: center; margin-top: 15px;">
                        <span style="font-size: 14px; color: #ccc;">Qo'lga tegadigan summa:</span><br>
                        <b style="font-size: 24px; color: #00f2ff;">{netto:,.0f} so'm</b>
                    </div>
                </div>
                """
            except (ValueError, ZeroDivisionError):
                res_html = "<div style='color: #ff4747; margin-bottom: 20px; text-align:center;'>Xatolik: Sonlarni to'g'ri kiriting!</div>"

        # KALKULYATOR HTML (ORQA FON QO'SHILDI)
        html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Oylik Hisoblash</title>
            <style>
                body {{ margin: 0; padding: 0; min-height: 100vh; font-family: 'Segoe UI', sans-serif; background: #000; display: flex; justify-content: center; align-items: center; color: #fff; }}
                .main-bg {{
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("/static/image.jpg");
                    background-size: cover; background-position: center; z-index: -1; filter: brightness(0.4);
                }}
                .box {{
                    background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(25px);
                    padding: 30px; border-radius: 30px; width: 90%; max-width: 400px;
                    border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                    margin: 20px 0;
                }}
                h2 {{ color: #00f2ff; text-align: center; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px; }}
                label {{ font-size: 12px; color: #ccc; margin-left: 10px; display: block; margin-top: 10px; }}
                input {{
                    width: 100%; padding: 12px; margin: 5px 0; border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.1); background: rgba(255, 255, 255, 0.05);
                    color: #fff; box-sizing: border-box; outline: none;
                }}
                input:focus {{ border-color: #00f2ff; }}
                .btn-calc {{
                    width: 100%; padding: 15px; border-radius: 25px; border: none;
                    background: #00f2ff; color: #000; font-weight: bold; cursor: pointer;
                    transition: 0.3s; margin-top: 20px;
                }}
                .btn-calc:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 242, 255, 0.4); }}
                .btn-back {{
                    display: block; text-align: center; color: #ccc; text-decoration: none;
                    margin-top: 20px; font-size: 13px;
                }}
            </style>
        </head>
        <body>
            <div class="main-bg"></div>
            <div class="box">
                <h2>{int(bonus_rate * 100)}% Kalkulyator</h2>

                {res_html}

                <form method="GET">
                    <label>Shtat oyligi (Summa):</label>
                    <input type="number" name="salary" step="any" required placeholder="Masalan: 4500000">

                    <label>Norma ish soati:</label>
                    <input type="number" name="norma_soat" step="any" required placeholder="Masalan: 160">

                    <label>Haqiqatda ishlangan soat:</label>
                    <input type="number" name="ishlangan_soat" step="any" required placeholder="Masalan: 168">

                    <label>Tungi soat:</label>
                    <input type="number" name="tungi_soat" step="any" value="0">

                    <label>Bayram soati:</label>
                    <input type="number" name="bayram_soati" step="any" value="0">

                    <button type="submit" class="btn-calc">HISOBLASH</button>
                </form>
                <a href="/okladmenu/" class="btn-back">← Orqaga qaytish</a>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)
def render_salary_page(user, natija_html):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Oylik Hisoblash</title>
        <style>
            body {{ margin: 0; padding: 0; background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
            .bg {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: url('/static/image.jpg') center/cover; filter: brightness(0.3); z-index: -1; }}
            .box {{ background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); padding: 30px; border-radius: 30px; width: 350px; border: 1px solid rgba(255,255,255,0.1); }}
            input {{ width: 100%; padding: 12px; margin: 10px 0; border-radius: 15px; border: none; background: rgba(255,255,255,0.1); color: #fff; }}
            button {{ width: 100%; padding: 15px; border-radius: 20px; border: none; background: #00f2ff; font-weight: bold; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="bg"></div>
        <div class="box">
            <h2 style="text-align:center; color:#00f2ff;">Oylik Hisoblash</h2>
            <p style="text-align:center; font-size:12px;">Razryad: {user.razryad}</p>
            {natija_html}
            <form method="GET">
                <input type="number" name="salary" placeholder="Shtat oyligi" required>
                <input type="number" name="norma_soat" placeholder="Norma soat" required>
                <input type="number" name="ishlangan_soat" placeholder="Ishlangan soat" required>
                <input type="number" name="tungi_soat" placeholder="Tungi soat">
                <input type="number" name="bayram_soati" placeholder="Bayram soati">
                <button type="submit">HISOBLASH</button>
            </form>
            <br>
            <a href="/second/" style="color:#ccc; text-decoration:none; display:block; text-align:center;">← Orqaga</a>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
def login_view(request):
    error_msg = ""
    login_val = ""
    show_verify = False

    if request.method == "POST":
        login_val = request.POST.get('login')
        password_val = request.POST.get('password')

        # Bazadan izlash
        user = UserProfile.objects.filter(login=login_val, password=password_val).first()

        if user:
            print(f"Foydalanuvchi topildi: {user.login}, Holati: {user.is_active}")
            if user.is_active:
                request.session['user_login'] = user.login
                return redirect('/second/')
            else:
                # MUHIM: Mana shu yerda biz xabarni yoqamiz
                error_msg = "Tasdiqlash kodingiz muddati tugagan! Yangi kod oling."
                show_verify = True
        else:
            error_msg = "Login yoki parol xato!"

    # HTML dizaynni shakllantirish
    token = get_token(request)
    bg_url = static('image.jpg')

    # Xato xabari bloki
    error_html = ""
    if error_msg:
        if show_verify:
            # Muddati tugaganlar uchun bot tugmasi bilan
            error_html = f"""
                <div style="background: rgba(255, 71, 71, 0.15); border: 1px solid #ff4747; padding: 15px; border-radius: 15px; margin-top: 20px;">
                    <p style="color: #ff4747; margin: 0 0 10px 0; font-size: 14px; font-weight: bold;">{error_msg}</p>
                    <a href="https://t.me/SizningBotUsername" target="_blank" style="display: block; background: #0088cc; color: white; padding: 10px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-bottom: 10px;">
                        <i class="fab fa-telegram"></i> Telegram Botga o'tish
                    </a>
                    <a href="/verify-code/?login={login_val}" style="color: #00f2ff; font-size: 13px;">Kodni kiritish -></a>
                </div>
                """
        else:
            # Oddiy login xatosi uchun
            error_html = f'<p style="color: #ff4747; margin-top: 20px; font-weight: bold;">{error_msg}</p>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Kirish</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ margin: 0; height: 100vh; display: flex; justify-content: center; align-items: center; background: #000; font-family: sans-serif; }}
            .bg {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: url('{bg_url}') center/cover; filter: brightness(0.3); z-index: -1; }}
            .card {{ background: rgba(255,255,255,0.08); backdrop-filter: blur(15px); padding: 40px; border-radius: 30px; width: 340px; text-align: center; border: 1px solid rgba(255,255,255,0.1); color: white; }}
            input {{ width: 100%; padding: 14px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2); background: rgba(0,0,0,0.3); color: white; margin-bottom: 15px; box-sizing: border-box; }}
            .btn {{ width: 100%; padding: 14px; border-radius: 12px; border: none; background: #00f2ff; color: #000; font-weight: bold; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="bg"></div>
        <div class="card">
            <h2 style="letter-spacing: 3px;">KIRISH</h2>
            <form method="POST">
                <input type="hidden" name="csrfmiddlewaretoken" value="{token}">
                <input type="text" name="login" placeholder="Login" value="{login_val}" required>
                <input type="password" name="password" placeholder="Parol" required>
                <button type="submit" class="btn">KIRISH</button>
            </form>
            {error_html}
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
def second_view(request):
    # 1. Sessiyani tekshirish
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/login/')

    # 2. Bazadan userni olish
    user = UserProfile.objects.filter(login=user_login).first()

    # 3. Aktivlikni tekshirish (30 kunlik muddat)
    if not user or not user.is_active:
        if 'user_login' in request.session:
            del request.session['user_login']
        return redirect('/login/')

    # 4. Ma'lumotlarni tayyorlash
    bg_url = static('image.jpg')
    avatar_url = user.image.url if hasattr(user, 'image') and user.image else static('default_avatar.png')
    display_name = user.full_name if user.full_name else user.login

    # 5. HTML dizayn (Funksiya ichida bo'lishi shart!)
    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bosh Menyu</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                :root {{
                    --bg: #0f0f0f; --header-bg: rgba(15, 15, 15, 0.9);
                    --txt: #ffffff; --card: rgba(255, 255, 255, 0.1);
                    --accent: #00f2ff; --border: rgba(255,255,255,0.1);
                }}
                [data-theme="light"] {{
                    --bg: #f2f2f2; --header-bg: rgba(255, 255, 255, 0.9);
                    --txt: #000000; --card: #ffffff;
                    --accent: #0072ff; --border: rgba(0,0,0,0.1);
                }}
                body {{
                    margin: 0; background: var(--bg); color: var(--txt);
                    font-family: 'Segoe UI', sans-serif; transition: 0.3s;
                }}
                .main-bg {{
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{bg_url}");
                    background-size: cover; background-position: center; z-index: -1;
                }}
                [data-theme="light"] .main-bg {{ display: none; }}
                .header {{
                    position: sticky; top: 0; display: flex; justify-content: space-between;
                    align-items: center; padding: 15px 20px; background: var(--header-bg);
                    backdrop-filter: blur(10px); z-index: 1000; border-bottom: 1px solid var(--border);
                }}
                .theme-toggle {{ cursor: pointer; font-size: 20px; color: var(--accent); margin-right: 15px; }}
                .container {{ padding: 20px; padding-bottom: 100px; max-width: 500px; margin: 0 auto; }}
                .menu-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
                .menu-card {{
                    background: var(--card); border-radius: 18px; padding: 20px;
                    text-align: center; text-decoration: none; color: var(--txt);
                    border: 1px solid var(--border); transition: 0.2s;
                    display: flex; flex-direction: column; align-items: center; gap: 10px;
                }}
                .menu-card:active {{ transform: scale(0.95); }}
                .menu-card i {{ font-size: 28px; color: var(--accent); }}
                .bottom-nav {{
                    position: fixed; bottom: 0; width: 100%; background: var(--header-bg);
                    display: flex; justify-content: space-around; padding: 12px 0;
                    border-top: 1px solid var(--border);
                }}
                .nav-item {{ text-decoration: none; color: #888; font-size: 11px; text-align: center; }}
                .nav-item.active {{ color: var(--accent); }}
            </style>
        </head>
        <body>
            <div class="main-bg"></div>
            <div class="header">
                <div style="font-weight:900; color:var(--accent);">TEMIR YO'L</div>
                <div style="display:flex; align-items:center;">
                    <i class="fas fa-moon theme-toggle" id="theme-btn" onclick="toggleTheme()"></i>
                    <a href="/profile/" style="display:flex; align-items:center; text-decoration:none; color:var(--txt);">
                        <span style="margin-right:8px; font-size:14px;">{display_name}</span>
                        <img src="{avatar_url}" style="width:32px; height:32px; border-radius:50%; border:1px solid var(--accent); object-fit: cover;">
                    </a>
                </div>
            </div>
            <div class="container">
                <div class="menu-grid">
                    <a href="/okladmenu/" class="menu-card"><i class="fas fa-coins"></i><span>Oylik</span></a>
                    <a href="/hisobot/" class="menu-card"><i class="fas fa-chart-line"></i><span>1 oylik hisobotim</span></a>
                    <a href="https://t.me/+HxJsZu-uZJA2NzBi" class="menu-card"><i class="fab fa-telegram"></i><span>Telegram Kanal</span></a>
                    <a href="/profile/" class="menu-card"><i class="fas fa-sliders"></i><span>Sozlamalar</span></a>
                    <a href="/chats/" class="menu-card"><i class="fas fa-comments"></i><span>Chatlar</span></a>
                    <a href="https://t.me/+IizmDY0I_4BkYzQy" class="menu-card"><i class="fas fa-headset"></i><span>Murojaat qiling</span></a>
                </div>
            </div>
            <div class="bottom-nav">
                <a href="/second/" class="nav-item active"><i class="fas fa-home"></i><br>Asosiy</a>
                <a href="/okladmenu/" class="nav-item"><i class="fas fa-calculator"></i><br>Hisoblar</a>
                <a href="/profile/" class="nav-item"><i class="fas fa-user"></i><br>Profil</a>
            </div>
            <script>
                function toggleTheme() {{
                    const body = document.documentElement;
                    const btn = document.getElementById('theme-btn');
                    if (body.getAttribute('data-theme') === 'light') {{
                        body.setAttribute('data-theme', 'dark');
                        btn.className = 'fas fa-moon theme-toggle';
                        localStorage.setItem('theme', 'dark');
                    }} else {{
                        body.setAttribute('data-theme', 'light');
                        btn.className = 'fas fa-sun theme-toggle';
                        localStorage.setItem('theme', 'light');
                    }}
                }}
                if (localStorage.getItem('theme') === 'light') {{
                    document.documentElement.setAttribute('data-theme', 'light');
                    document.getElementById('theme-btn').className = 'fas fa-sun theme-toggle';
                }}
            </script>
        </body>
        </html>
        """
    return HttpResponse(html)
def profile_view(request):
    # 1. Sessiya va Userni tekshirish
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/')

    user = UserProfile.objects.filter(login=user_login).first()
    if not user:
        return redirect('/')

    # 2. Ma'lumotlarni yangilash (POST)
    if request.method == "POST":
        new_name = request.POST.get('display_name')
        new_pic = request.FILES.get('profile_pic')

        if new_name:
            user.login = new_name
        if new_pic:
            user.image = new_pic  # Buning uchun models.py da image field bo'lishi shart

        user.save()
        request.session['user_login'] = user.login
        return redirect('/profile/')

    # 3. Kerakli o'zgaruvchilarni yaratish (Xatolik bermasligi uchun)
    # Rasm modelda bo'lsa uni oladi, bo'lmasa default rasmni oladi
    avatar_url = user.image.url if hasattr(user, 'image') and user.image else static('default_avatar.png')
    bg_url = static('image.jpg')  # NameError bermasligi uchun aniq belgilandi
    token = get_token(request)
    # Razryad modelda bo'lsa oladi, bo'lmasa 'Noma'lum' deb chiqaradi
    user_razryad = getattr(user, 'razryad', 'Kiritilmagan')

    # 4. HTML Dizayn
    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Profil | {user.login}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ margin: 0; min-height: 100vh; display: flex; justify-content: center; align-items: center; background: #000; font-family: 'Segoe UI', sans-serif; color: white; padding: 20px; }}
            .bg-image {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-image: url('{bg_url}'); background-size: cover; filter: brightness(0.2); z-index: -1; }}

            .profile-card {{
                background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(25px);
                padding: 30px; border-radius: 40px; width: 100%; max-width: 380px; text-align: center;
                border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            }}

            .avatar-container {{ position: relative; width: 110px; height: 110px; margin: 0 auto 15px; }}
            .avatar {{ width: 110px; height: 110px; border-radius: 50%; object-fit: cover; border: 3px solid #00f2ff; }}

            .upload-btn {{
                position: absolute; bottom: 0; right: 0; background: #00f2ff; color: #000;
                width: 30px; height: 30px; border-radius: 50%; display: flex; justify-content: center;
                align-items: center; cursor: pointer; font-size: 18px; font-weight: bold;
            }}

            h2 {{ color: #fff; margin: 10px 0 5px; letter-spacing: 1px; }}
            .razryad-badge {{ background: rgba(0, 242, 255, 0.1); color: #00f2ff; padding: 5px 15px; border-radius: 12px; font-size: 14px; font-weight: bold; margin-bottom: 10px; display: inline-block; border: 1px solid rgba(0, 242, 255, 0.2); }}
            .tabel-label {{ color: rgba(255,255,255,0.5); font-size: 12px; margin-bottom: 25px; display: block; }}

            .input-group {{ text-align: left; margin-bottom: 20px; }}
            label {{ font-size: 12px; color: #aaa; margin-left: 15px; }}
            input[type="text"] {{
                width: 100%; padding: 12px 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);
                background: rgba(255,255,255,0.05); color: #fff; outline: none; box-sizing: border-box; margin-top: 5px;
            }}

            .save-btn {{
                width: 100%; padding: 14px; border-radius: 20px; border: none;
                background: #00f2ff; color: #000; font-weight: bold; cursor: pointer; transition: 0.3s;
                text-transform: uppercase; letter-spacing: 1px;
            }}
            .save-btn:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 242, 255, 0.3); }}

            .logout-btn {{
                display: flex; align-items: center; justify-content: center; gap: 8px;
                width: 100%; margin-top: 15px; padding: 12px; border-radius: 20px;
                background: rgba(255, 71, 71, 0.1); color: #ff4747;
                text-decoration: none; font-size: 14px; font-weight: 600;
                border: 1px solid rgba(255, 71, 71, 0.2); transition: 0.3s;
            }}
        </style>
    </head>
    <body>
        <div class="bg-image"></div>
        <div class="profile-card">
            <form method="POST" enctype="multipart/form-data">
                <input type="hidden" name="csrfmiddlewaretoken" value="{token}">

                <div class="avatar-container">
                    <img src="{avatar_url}" class="avatar" id="preview">
                    <label for="file-upload" class="upload-btn"><i class="fas fa-camera" style="font-size: 14px;"></i></label>
                    <input id="file-upload" name="profile_pic" type="file" style="display:none;" onchange="previewImage(this)">
                </div>

                <h2>{user.login}</h2>
                <div class="razryad-badge"><i class="fas fa-award"></i> Razryad: {user_razryad}</div>
                <span class="tabel-label">Tabel raqami: {user.tabel_raqami}</span>

                <div class="input-group">
                    <label>Foydalanuvchi nomi:</label>
                    <input type="text" name="display_name" value="{user.login}">
                </div>

                <button type="submit" class="save-btn">O'zgarishlarni saqlash</button>
            </form>

            <a href="/logout/" class="logout-btn"><i class="fas fa-sign-out-alt"></i> Tizimdan chiqish</a>
            <a href="/second/" style="color: rgba(255,255,255,0.4); text-decoration:none; display:block; margin-top:15px; font-size:13px;">Asosiy sahifa</a>
        </div>

        <script>
            function previewImage(input) {{
                if (input.files && input.files[0]) {{
                    var reader = new FileReader();
                    reader.onload = function(e) {{
                        document.getElementById('preview').src = e.target.result;
                    }}
                    reader.readAsDataURL(input.files[0]);
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def chats(request):
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/')

    current_user = UserProfile.objects.filter(login=user_login).first()

    # 1. POST so'rovlarini qayta ishlash
    if request.method == "POST":
        delete_id = request.POST.get('delete_id')
        if delete_id:
            msg = ChatMessage.objects.filter(id=delete_id, user=current_user).first()
            if msg:
                msg.delete()
                return HttpResponse("OK")

        text = request.POST.get('text')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        voice = request.FILES.get('voice')

        if current_user:
            ChatMessage.objects.create(
                user=current_user, text=text, image=image, video=video, voice=voice
            )
            return HttpResponse("OK")

    # 2. Ma'lumotlarni yig'ish
    messages = ChatMessage.objects.all().order_by('created_at')
    csrf_token_value = get_token(request)

    # STATIC YO'LI: rasm static papkangizda 'image.jpg' nomi bilan bo'lishi kerak
    bg_url = static('image.jpg')

    msg_list_html = ""
    for m in messages:
        is_me = m.user.login == user_login
        wrapper_class = "my-wrapper" if is_me else "other-wrapper"
        bubble_class = "my-bubble" if is_me else "other-bubble"

        options = ""
        if is_me:
            options = f'''
                <div class="msg-options" onclick="event.stopPropagation(); toggleMenu({m.id})">
                    <i class="fas fa-ellipsis-v"></i>
                    <div class="options-menu" id="menu-{m.id}">
                        <button onclick="deleteMsg({m.id})"><i class="fas fa-trash"></i> O'chirish</button>
                    </div>
                </div>'''

        media = ""
        if m.image: media += f'<img src="{m.image.url}" class="msg-media">'
        if m.video: media += f'<video src="{m.video.url}" controls class="msg-media"></video>'
        if m.voice: media += f'<audio src="{m.voice.url}" controls style="max-width: 100%;"></audio>'

        msg_list_html += f'''
            <div class="message-wrapper {wrapper_class}" id="msg-{m.id}">
                <img src="{m.user.image.url if m.user.image else ''}" class="user-avatar">
                <div class="msg-bubble {bubble_class}">
                    {media}
                    <div class="msg-text">{m.text if m.text else ''}</div>
                    <span class="msg-time">{m.created_at.strftime('%H:%M')}</span>
                </div>
                {options}
            </div>'''

    # 3. HTML VA CSS (To'liq optimallashtirilgan)
    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <title>TemirYo'l Chati</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}

            html, body {{
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }}

            body {{
                display: flex;
                flex-direction: column;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                /* ORQA FONNI SHU YERDA BELGILAYMIZ */
                background-color: #0e1621;
                background-image: linear-gradient(rgba(14, 22, 33, 0.7), rgba(14, 22, 33, 0.7)), url('{bg_url}');
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            }}

            /* Header */
            .chat-header {{
                background: rgba(23, 33, 43, 0.95);
                padding: 10px 15px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                color: white;
                z-index: 10;
                height: 56px;
                flex-shrink: 0;
                backdrop-filter: blur(10px);
            }}
            .header-center h3 {{ margin: 0; font-size: 18px; }}
            .header-center p {{ margin: 0; font-size: 12px; color: #40a7e3; }}
            .back-btn {{ color: #6c7883; font-size: 20px; text-decoration: none; }}

            /* Chat maydoni */
            .chat-messages {{
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                display: flex;
                flex-direction: column;
                gap: 12px;
                background: transparent !important;
                -webkit-overflow-scrolling: touch;
            }}

            .message-wrapper {{ display: flex; align-items: flex-end; gap: 8px; max-width: 85%; position: relative; }}
            .my-wrapper {{ align-self: flex-end; flex-direction: row-reverse; }}
            .user-avatar {{ width: 35px; height: 35px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }}

            .msg-bubble {{
                padding: 8px 12px;
                border-radius: 16px;
                font-size: 15px;
                color: white;
                word-wrap: break-word;
                box-shadow: 0 1px 2px rgba(0,0,0,0.3);
            }}
            .my-bubble {{ background: rgba(43, 82, 120, 0.95); border-bottom-right-radius: 4px; }}
            .other-bubble {{ background: rgba(24, 37, 51, 0.95); border-bottom-left-radius: 4px; }}

            .msg-media {{ max-width: 100%; border-radius: 10px; margin-bottom: 5px; display: block; }}
            .msg-time {{ font-size: 10px; opacity: 0.6; float: right; margin-top: 4px; margin-left: 8px; }}

            /* Input Area (Mobil uchun fix) */
            .input-area {{
                background: rgba(23, 33, 43, 0.95);
                padding: 8px 12px;
                display: flex;
                align-items: center;
                gap: 10px;
                flex-shrink: 0;
                padding-bottom: calc(8px + env(safe-area-inset-bottom));
                backdrop-filter: blur(10px);
                z-index: 100;
            }}

            .input-wrapper {{
                flex: 1;
                background: rgba(36, 47, 61, 0.8);
                border-radius: 22px;
                padding: 0 15px;
                display: flex;
                align-items: center;
                min-height: 42px;
            }}

            .message-input {{
                flex: 1;
                background: transparent;
                border: none;
                color: white;
                outline: none;
                font-size: 16px;
                padding: 10px 0;
            }}

            .icon-btn {{ color: #6c7883; font-size: 22px; cursor: pointer; }}
            .send-btn {{ background: none; border: none; color: #40a7e3; font-size: 24px; cursor: pointer; }}

            /* Menyu */
            .msg-options {{ color: #6c7883; cursor: pointer; padding: 5px; }}
            .options-menu {{
                display: none; position: absolute; background: #1c2938;
                border-radius: 8px; right: 0; top: 25px; width: 120px; z-index: 100;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }}
            .options-menu button {{
                width: 100%; background: none; border: none; color: white;
                padding: 12px; text-align: left; cursor: pointer;
            }}

            .visualizer {{ display: none; flex: 1; align-items: center; gap: 2px; height: 20px; }}
            .bar {{ width: 2px; background: #40a7e3; border-radius: 1px; min-height: 3px; }}
        </style>
    </head>
    <body>
        <div class="chat-header">
            <div class="header-side"><a href="/second/" class="back-btn"><i class="fas fa-arrow-left"></i></a></div>
            <div class="header-center"><h3>TemirYo'l chati</h3><p>online</p></div>
            <div class="header-side"></div>
        </div>

        <div class="chat-messages" id="chatContainer">{msg_list_html}</div>

        <div class="input-area">
            <input type="file" id="fileInp" style="display:none" onchange="upFile()">
            <i class="fas fa-paperclip icon-btn" onclick="document.getElementById('fileInp').click()"></i>
            <div class="input-wrapper">
                <input type="text" id="msgInp" class="message-input" placeholder="Xabar..." autocomplete="off">
                <div id="viz" class="visualizer"></div>
            </div>
            <i class="fas fa-microphone icon-btn" id="micBtn"></i>
            <button class="send-btn" onclick="hSend()"><i class="fas fa-paper-plane"></i></button>
        </div>

        <script>
            const chat = document.getElementById('chatContainer');
            chat.scrollTop = chat.scrollHeight;

            function toggleMenu(id) {{
                document.querySelectorAll('.options-menu').forEach(m => {{ if(m.id !== 'menu-'+id) m.style.display = 'none'; }});
                const m = document.getElementById('menu-'+id);
                m.style.display = m.style.display === 'block' ? 'none' : 'block';
            }}
            window.onclick = () => document.querySelectorAll('.options-menu').forEach(m => m.style.display='none');

            async function deleteMsg(id) {{
                const fd = new FormData(); fd.append('delete_id', id);
                fd.append('csrfmiddlewaretoken', '{csrf_token_value}');
                await fetch('', {{method:'POST', body:fd}});
                document.getElementById('msg-'+id).remove();
            }}

            let rec, chunks = [], aCtx, analyser, data, anim;
            const viz = document.getElementById('viz'), inp = document.getElementById('msgInp'), mBtn = document.getElementById('micBtn');
            for(let i=0; i<25; i++) {{ const b=document.createElement('div'); b.className='bar'; viz.appendChild(b); }}

            mBtn.onclick = async () => {{
                try {{
                    if(!rec || rec.state === 'inactive') {{
                        const s = await navigator.mediaDevices.getUserMedia({{audio:true}});
                        rec = new MediaRecorder(s); chunks = [];
                        inp.style.display='none'; viz.style.display='flex'; mBtn.style.color='#ff4b4b';
                        aCtx = new (window.AudioContext || window.webkitAudioContext)();
                        const src = aCtx.createMediaStreamSource(s);
                        analyser = aCtx.createAnalyser(); src.connect(analyser); analyser.fftSize=64;
                        data = new Uint8Array(analyser.frequencyBinCount);
                        function draw() {{
                            anim = requestAnimationFrame(draw); analyser.getByteFrequencyData(data);
                            document.querySelectorAll('.bar').forEach((b,i)=> b.style.height=((data[i%data.length]/255)*20+4)+'px');
                        }}
                        draw(); rec.ondataavailable = e => chunks.push(e.data); rec.start();
                    }} else {{ stopRec(); }}
                }} catch(e) {{ alert("Mikrofon ruxsati berilmadi"); }}
            }};

            function stopRec() {{
                if(rec && rec.state !== 'inactive') {{
                    rec.stop(); cancelAnimationFrame(anim); if(aCtx) aCtx.close();
                    mBtn.style.color='#6c7883'; viz.style.display='none'; inp.style.display='block';
                }}
            }}

            async function hSend() {{
                const fd = new FormData(); fd.append('csrfmiddlewaretoken', '{csrf_token_value}');
                if(rec && rec.state === 'recording') {{
                    rec.onstop = async () => {{
                        fd.append('voice', new Blob(chunks, {{type:'audio/mp3'}}), 'v.mp3');
                        await fetch('', {{method:'POST', body:fd}}); location.reload();
                    }};
                    stopRec();
                }} else {{
                    if(!inp.value.trim()) return;
                    fd.append('text', inp.value);
                    await fetch('', {{method:'POST', body:fd}}); location.reload();
                }}
            }}

            async function upFile() {{
                const f = document.getElementById('fileInp').files[0];
                if(!f) return;
                const fd = new FormData(); fd.append('csrfmiddlewaretoken', '{csrf_token_value}');
                if(f.type.startsWith('image')) fd.append('image', f);
                else if(f.type.startsWith('video')) fd.append('video', f);
                await fetch('', {{method:'POST', body:fd}}); location.reload();
            }}
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def logout_view(request):
    request.session.flush()
    return redirect('../') # Login sahifasiga qaytarish
def delete_message(request, msg_id):
    if request.method == "POST":
        msg = ChatMessage.objects.filter(id=msg_id).first()
        # Faqat o'z xabarini yoki admin o'chira olishi uchun:
        user_login = request.session.get('user_login')
        if msg and msg.user.login == user_login:
            msg.delete()
            return HttpResponse("OK")
    return HttpResponse("Xato", status=400)
def login(request):
    error_message = ""
    bg_url = static('image.jpg')

    if request.method == "POST":
        u = request.POST.get('u_name')
        p = request.POST.get('p_val')
        user = UserProfile.objects.filter(login=u, password=p).first()

        if user:
            # --- MUDDATNI TEKSHIRISH QISMI ---
            bugun = datetime.now(timezone.utc)
            ruyxatdan_utgan = getattr(user, 'created_at', bugun)
            is_paid = getattr(user, 'is_paid', False)

            # Agar to'lov qilgan bo'lsa 30 kun, qilmagan bo'lsa 3 kun ruxsat
            ruxsat_muddati = 30 if is_paid else 3
            farq = bugun - ruyxatdan_utgan

            if farq.days >= ruxsat_muddati:
                # Muddat tugagan bo'lsa, login qildirmaymiz va xato chiqaramiz
                error_message = """
                            <div class="error-box" style="background: rgba(255, 165, 0, 0.15); color: #ffa500; border-color: #ffa500;">
                                <i class="fas fa-clock"></i>
                                Foydalanish muddati tugagan! Davom etish uchun to'lov qiling.
                            </div>
                        """
            else:
                # Muddat bor bo'lsa, ichkariga kiritamiz
                request.session['user_login'] = user.login
                return redirect('/second/')
        else:
            error_message = """
                        <div class="error-box">
                            <i class="fas fa-exclamation-circle"></i>
                            Login yoki parol xato!
                        </div>
                    """

    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Kirish | TemirYo'l</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                * {{ box-sizing: border-box; font-family: 'Segoe UI', Roboto, sans-serif; }}
                body {{
                    margin: 0; height: 100vh; display: flex; flex-direction: column;
                    justify-content: center; align-items: center; background-color: #0f0f0f;
                }}
                .bg-image {{
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background-image: url('{bg_url}'); background-size: cover; background-position: center;
                    filter: brightness(0.2); z-index: -1;
                }}

                .login-card {{
                    background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(20px);
                    padding: 30px; border-radius: 28px; width: 90%; max-width: 400px;
                    border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;
                }}

                .brand-name {{ font-size: 24px; font-weight: 800; color: #fff; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 25px; }}

                input {{
                    width: 100%; padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
                    background: rgba(255,255,255,0.05); color: #fff; margin-bottom: 15px; outline: none;
                }}

                .login-btn {{
                    width: 100%; padding: 15px; border-radius: 12px; border: none;
                    background: linear-gradient(135deg, #00f2ff, #0072ff);
                    color: #fff; font-weight: bold; cursor: pointer; text-transform: uppercase;
                }}

                .error-box {{
                    background: rgba(255, 71, 71, 0.15); color: #ff4747; padding: 12px;
                    border-radius: 12px; margin-bottom: 20px; font-size: 13px; border: 1px solid rgba(255, 71, 71, 0.3);
                    display: flex; align-items: center; justify-content: center; gap: 8px;
                }}

                /* --- TO'LOV TIZIMI (LOGIN PASTIDA) --- */
                .payment-card {{
                    margin-top: 20px; background: rgba(255, 215, 0, 0.05);
                    padding: 20px; border-radius: 28px; width: 90%; max-width: 400px;
                    border: 1px solid rgba(255, 215, 0, 0.2); text-align: center;
                }}
                .card-grid {{ display: flex; justify-content: space-around; margin: 15px 0; }}
                .card-item {{ background: #fff; color: #000; padding: 8px; border-radius: 8px; width: 75px; font-size: 10px; font-weight: bold; }}
                .pay-link {{
                    display: block; width: 100%; padding: 12px; background: #ffd700;
                    color: #000; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="bg-image"></div>

            <div class="login-card">
                <div class="brand-name">Temir Yo'l</div>
                {error_message}
                <form method="POST">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">
                    <input type="text" name="u_name" placeholder="Foydalanuvchi nomi" required>
                    <input type="password" name="p_val" placeholder="Parol" required>
                    <button type="submit" class="login-btn">Tizimga kirish</button>
                </form>
                <div style="margin-top: 15px;">
                    <a href="/signup/" style="color: rgba(255,255,255,0.6); text-decoration: none; font-size: 13px;">Ro'yxatdan o'tish</a>
                </div>
            </div>
            </div>
        </body>
        </html>
        """
    return HttpResponse(html)
def register_view(request):
    if request.method == "POST":
        login = request.POST.get('login')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        check_file = request.FILES.get('check_img')

        if UserProfile.objects.filter(login=login).exists():
            return HttpResponse("Bu login band!")

        # 1. Foydalanuvchini bazada yaratish (is_active=False)
        user = UserProfile.objects.create(
            login=login,
            password=password,  # Aslida hash qilish kerak: make_password(password)
            phone=phone,
            is_active=False
        )

        # 2. Telegramga Adminga yuborish
        bot_token = "7833987841:AAE6GjAu_w8AAP97ZMmbzAy7x5y9dLa7ymM"
        admin_id = "8513245980"  # O'zingizning ID'ingizni yozing

        caption = f"🚀 Yangi so'rov!\n👤 Login: {login}\n🔑 Parol: {password}\n📞 Tel: {phone}"

        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ Tasdiqlash", "callback_data": f"accept_{user.id}"},
                {"text": "❌ Rad etish", "callback_data": f"reject_{user.id}"}
            ]]
        }

        files = {'photo': check_file}
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendPhoto", data={
            "chat_id": admin_id,
            "caption": caption,
            "reply_markup": json.dumps(keyboard)
        }, files=files)

        return HttpResponse("So'rovingiz yuborildi. Admin tasdiqlashini kuting.")

        # Oddiy HTML Forma (Dizaynni o'zingiz moslab olasiz)
    return render(request, 'register.html')
def signup(request):
    bg_image_url = static('image.jpg')  # Statik rasm yo'li

    if request.method == "POST":
        u = request.POST.get('u_name')
        p = request.POST.get('p_val')
        tel = request.POST.get('tel_val')
        tabel = request.POST.get('t_raqam')
        fname = request.POST.get('full_name')
        raz_val = request.POST.get('razryad')

        # Okladni server tomonida ham tekshirish (Xavfsizlik uchun)
        tariflar = {"5/3": 5336929, "5/2": 4800000, "4/3": 4100000}
        oklad_val = tariflar.get(raz_val, 0)

        if UserProfile.objects.filter(login=u).exists():
            return HttpResponse("❌ Bu login band!")

        if u and p and tel:
            UserProfile.objects.create(
                login=u, password=p, phone=tel,
                tabel_raqami=tabel, full_name=fname,
                razryad=raz_val, oklad=oklad_val,
                is_active=False
            )
            return redirect(f'/verify-code/?login={u}')

    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    margin: 0; padding: 0;
                    background: url('{bg_image_url}') no-repeat center center fixed; 
                    background-size: cover; height: 100vh;
                    display: flex; justify-content: center; align-items: center;
                    font-family: 'Segoe UI', sans-serif;
                }}
                body::before {{
                    content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0, 0, 0, 0.65); z-index: 1;
                }}
                .container {{ 
                    position: relative; z-index: 2;
                    background: rgba(255, 255, 255, 0.1); 
                    padding: 30px; border-radius: 20px; width: 360px; 
                    border: 1px solid rgba(255, 255, 255, 0.2); 
                    backdrop-filter: blur(15px); box-shadow: 0 15px 35px rgba(0,0,0,0.5);
                    text-align: center; color: white;
                }}
                input {{ 
                    width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px; 
                    border: 1px solid #444; background: rgba(0, 0, 0, 0.7); 
                    color: white; box-sizing: border-box; outline: none;
                }}
                .oklad-info {{
                    background: rgba(0, 242, 255, 0.15); padding: 10px;
                    border: 1px dashed #00f2ff; border-radius: 10px;
                    margin: 10px 0; color: #00f2ff; font-weight: bold;
                }}
                .btn {{ 
                    width: 100%; padding: 14px; border-radius: 10px; border: none; 
                    background: linear-gradient(90deg, #00f2ff, #0072ff); 
                    color: black; font-weight: bold; cursor: pointer; transition: 0.3s;
                }}
                .btn:hover {{ transform: scale(1.02); box-shadow: 0 0 15px #00f2ff; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Registratsiya</h2>
                <form method="POST">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">
                    <input type="text" name="full_name" placeholder="Ism-familiya" required>
                    <input type="text" name="u_name" placeholder="Login" required>
                    <input type="password" name="p_val" placeholder="Parol" required>
                    <input type="text" name="t_raqam" placeholder="Tabel raqami" required>
                    <input type="text" name="tel_val" placeholder="Telefon (+998...)" required>
                    <input type="text" id="razryad" name="razryad" placeholder="Razryad (Masalan: 5/3)" oninput="calc()" required>

                    <div class="oklad-info">
                        Oklad: <span id="res">0</span> so'm
                    </div>

                    <button type="submit" class="btn">RO'YXATDAN O'TISH</button>
                </form>
            </div>
            <script>
                function calc() {{
                    const val = document.getElementById('razryad').value;
                    const res = document.getElementById('res');
                    const prices = {{"5/3": 5336929, "5/2": 4800000, "4/3": 4100000}};
                    res.innerText = prices[val] ? prices[val].toLocaleString() : "0";
                }}
            </script>
        </body>
        </html>
        """
    return HttpResponse(html)
def verify_code_view(request):
    login_val = request.GET.get('login') or request.POST.get('login')
    user = UserProfile.objects.filter(login=login_val).first()

    if request.method == "POST":
        entered_code = request.POST.get('activation_code')
        if user and user.activation_code == entered_code:
            user.is_active = True
            user.save()
            request.session['user_login'] = user.login
            return redirect('/second/')
        else:
            return HttpResponse("Xato kod kiritildi!")

    # HTML Dizayn
    bg_url = static('image.jpg')
    token = get_token(request)

    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Aktivlashtirish</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ margin: 0; height: 100vh; display: flex; justify-content: center; align-items: center; background: #000; font-family: 'Segoe UI', sans-serif; }}
            .bg {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: url('{bg_url}') center/cover; filter: brightness(0.3); z-index: -1; }}
            .card {{ background: rgba(255,255,255,0.1); backdrop-filter: blur(20px); padding: 30px; border-radius: 30px; width: 320px; text-align: center; border: 1px solid rgba(255,255,255,0.2); color: white; }}
            .bot-btn {{ display: block; background: #0088cc; color: white; padding: 12px; border-radius: 15px; text-decoration: none; margin-bottom: 20px; font-weight: bold; }}
            input {{ width: 100%; padding: 12px; border-radius: 15px; border: none; background: rgba(255,255,255,0.1); color: white; margin-bottom: 15px; box-sizing: border-box; text-align: center; font-size: 18px; letter-spacing: 5px; }}
            button {{ width: 100%; padding: 12px; border-radius: 15px; border: none; background: #00f2ff; color: #000; font-weight: bold; cursor: pointer; }}
            .info {{ font-size: 13px; color: #ccc; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div class="bg"></div>
        <div class="card">
            <i class="fas fa-user-shield" style="font-size: 40px; color: #ff4747; margin-bottom: 15px;"></i>
            <h3>Profil faolsiz</h3>
            <p class="info">Profilingizni faollashtirish uchun Telegram botdan yangi kod oling.</p>

            <a href="https://t.me/SizningBotUsername" class="bot-btn">
                <i class="fab fa-telegram"></i> Kodni olish (Bot)
            </a>

            <form method="POST">
                <input type="hidden" name="csrfmiddlewaretoken" value="{token}">
                <input type="hidden" name="login" value="{login_val}">
                <input type="text" name="activation_code" placeholder="0000" required>
                <button type="submit">TASDIQLASH</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
def hisobot(request):
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/')

    current_user = UserProfile.objects.filter(login=user_login).first()
    if not current_user:
        return redirect('/')

    # Ma'lumotlarni olish
    jadval_malumotlari = WorkSchedule.objects.filter(user=current_user).order_by('-date')

    # Jami hisoblash (Norma qo'shilmaydi)
    jami = jadval_malumotlari.aggregate(
        t_ish=Sum('ishlagan_soati'),
        t_tungi=Sum('tungi_soati'),
        t_bayram=Sum('bayram_soati')
    )

    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body {{ background: #0e1621; color: white; font-family: sans-serif; margin: 0; padding: 15px; }}
                .header {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
                .back-btn {{ color: #40a7e3; text-decoration: none; font-size: 24px; }}
                .table-container {{ overflow-x: auto; background: #17212b; border-radius: 12px; border: 1px solid #242f3d; }}
                table {{ width: 100%; border-collapse: collapse; min-width: 800px; }}
                th, td {{ padding: 15px; text-align: center; border-bottom: 1px solid #242f3d; }}
                th {{ background: #2b5278; color: #40a7e3; font-size: 11px; text-transform: uppercase; }}
                .date-col {{ color: #8ab4f8; font-weight: bold; }}
                .total-row {{ background: #242f3d; font-weight: bold; border-top: 2px solid #40a7e3; color: #fff; }}
            </style>
        </head>
        <body>
            <div class="header">
                <a href="/second/" class="back-btn"><i class="fas fa-arrow-left"></i></a>
                <h3 style="margin:0;">Oylik Ish Hisoboti</h3>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Sana</th>
                            <th>Norma Soati</th> <th>Oklad</th>
                            <th>Ishlangan Soat</th>
                            <th>Tungi Soat</th>
                            <th>Bayram Soati</th>
                        </tr>
                    </thead>
                    <tbody>
        """

    last_oklad = 0
    last_norma = 0

    if jadval_malumotlari.exists():
        for row in jadval_malumotlari:
            last_oklad = row.oklad
            last_norma = row.norma_soati
            html += f"""
                    <tr>
                        <td class="date-col">{row.date}</td>
                        <td>{row.norma_soati}</td>
                        <td>{row.oklad}</td>
                        <td>{row.ishlagan_soati}</td>
                        <td>{row.tungi_soati}</td>
                        <td>{row.bayram_soati}</td>
                    </tr>
                """

        # JAMI QATORI (Norma qo'shilmaydi, faqat oxirgisi chiqadi)
        html += f"""
                    <tr class="total-row">
                        <td>JAMI:</td>
                        <td>{last_norma}</td>
                        <td>{last_oklad}</td>
                        <td>{jami['t_ish'] or 0}</td>
                        <td>{jami['t_tungi'] or 0}</td>
                        <td>{jami['t_bayram'] or 0}</td>
                    </tr>
            """
    else:
        html += "<tr><td colspan='6' style='padding:50px;'>Ma'lumotlar mavjud emas</td></tr>"

    html += "</tbody></table></div></body></html>"
    return HttpResponse(html)