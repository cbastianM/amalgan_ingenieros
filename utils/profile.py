# utils/profile.py - Gestion de fotos de perfil de usuario
import os
import base64
from PIL import Image

PROFILE_PHOTOS_DIR = "assets/profile_photos"
os.makedirs(PROFILE_PHOTOS_DIR, exist_ok=True)

AVATAR_ICONS = {
    "Director": "DIR",
    "Residente": "RES",
    "Almacenista": "ALM",
    "Controlador": "CON",
    "default": "USR"
}

def get_profile_photo_path(username):
    for ext in ['png', 'jpg', 'jpeg']:
        path = os.path.join(PROFILE_PHOTOS_DIR, f"{username}.{ext}")
        if os.path.exists(path):
            return path
    return None

def profile_photo_exists(username):
    return get_profile_photo_path(username) is not None

def get_default_avatar(rol):
    return AVATAR_ICONS.get(rol, AVATAR_ICONS["default"])

def render_profile_photo_html(username, rol, size="60px", show_border=True):
    photo_path = get_profile_photo_path(username)
    default_icon = get_default_avatar(rol)
    
    border_style = "border: 3px solid #C9A227;" if show_border else ""
    
    if photo_path and os.path.exists(photo_path):
        try:
            with open(photo_path, "rb") as f:
                img_bytes = f.read()
                encoded = base64.b64encode(img_bytes).decode()
            
            ext = photo_path.split('.')[-1].lower()
            mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            
            return f"""
            <div style="width:{size};height:{size};border-radius:50%;overflow:hidden;{border_style}box-shadow:0 2px 8px rgba(0,0,0,0.15);display:flex;align-items:center;justify-content:center;background:#F5F5F5">
                <img src="data:{mime};base64,{encoded}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">
            </div>
            """
        except:
            pass
    
    return f"""
    <div style="width:{size};height:{size};border-radius:50%;background:linear-gradient(135deg, #C9A227 0%, #B8941F 100%);{border_style}box-shadow:0 2px 8px rgba(0,0,0,0.15);display:flex;align-items:center;justify-content:center;font-size:calc({size} * 0.4);color:#FFFFFF;font-weight:bold">
        {default_icon}
    </div>
    """

def render_profile_card_html(username, nombre, rol, size="80px"):
    photo_path = get_profile_photo_path(username)
    default_icon = get_default_avatar(rol)
    
    if photo_path and os.path.exists(photo_path):
        try:
            with open(photo_path, "rb") as f:
                img_bytes = f.read()
                encoded = base64.b64encode(img_bytes).decode()
            
            ext = photo_path.split('.')[-1].lower()
            mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            
            return f"""
            <div style="text-align:center;padding:15px;background:linear-gradient(135deg, #FFFFFF 0%, #F8F8F8 100%);border:2px solid #E0E0E0;border-radius:12px;cursor:pointer" class="profile-card">
                <div style="width:{size};height:{size};border-radius:50%;overflow:hidden;margin:0 auto 10px;box-shadow:0 4px 12px rgba(0,0,0,0.2);border:3px solid #C9A227">
                    <img src="data:{mime};base64,{encoded}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">
                </div>
                <div style="font-size:14px;font-weight:700;color:#1A1A1A">{nombre}</div>
                <div style="font-size:12px;color:#666666;text-transform:uppercase;letter-spacing:0.5px">{rol}</div>
            </div>
            """
        except:
            pass
    
    return f"""
    <div style="text-align:center;padding:15px;background:linear-gradient(135deg, #FFFFFF 0%, #F8F8F8 100%);border:2px solid #E0E0E0;border-radius:12px;cursor:pointer" class="profile-card">
        <div style="width:{size};height:{size};border-radius:50%;background:linear-gradient(135deg, #C9A227 0%, #B8941F 100%);margin:0 auto 10px;box-shadow:0 4px 12px rgba(201,162,39,0.3);display:flex;align-items:center;justify-content:center;border:3px solid #C9A227">
            <span style="font-size:calc({size} * 0.35);color:#FFFFFF;font-weight:bold">{default_icon}</span>
        </div>
        <div style="font-size:14px;font-weight:700;color:#1A1A1A">{nombre}</div>
        <div style="font-size:12px;color:#666666;text-transform:uppercase;letter-spacing:0.5px">{rol}</div>
    </div>
    """

def save_profile_photo(username, uploaded_file):
    if uploaded_file is not None:
        for ext in ['png', 'jpg', 'jpeg']:
            old_path = os.path.join(PROFILE_PHOTOS_DIR, f"{username}.{ext}")
            if os.path.exists(old_path):
                os.remove(old_path)
        
        file_ext = uploaded_file.name.split('.')[-1].lower()
        new_path = os.path.join(PROFILE_PHOTOS_DIR, f"{username}.{file_ext}")
        
        with open(new_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        if file_ext in ['png', 'jpg', 'jpeg']:
            try:
                img = Image.open(new_path)
                max_size = (400, 400)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(new_path, optimize=True, quality=85)
            except:
                pass
        
        return True
    return False

def delete_profile_photo(username):
    for ext in ['png', 'jpg', 'jpeg']:
        path = os.path.join(PROFILE_PHOTOS_DIR, f"{username}.{ext}")
        if os.path.exists(path):
            os.remove(path)
            return True
    return False

def render_profile_photo_block(username, rol, size=60):
    """Render profile photo as a real image (no HTML)."""
    photo_path = get_profile_photo_path(username)
    if photo_path and os.path.exists(photo_path):
        import streamlit as st
        st.image(photo_path, width=size)
        return
    # Placeholder
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGBA", (size, size), (200, 200, 200, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([(4,4),(size-4,size-4)], fill=(120,120,120,255))
        initial = (str(username)[:1] or "?").upper()
        font = ImageFont.load_default()
        w, h = draw.textsize(initial, font=font)
        draw.text(((size-w)//2, (size-h)//2), initial, fill=(255,255,255,255), font=font)
        import streamlit as st
        st.image(img, width=size)
    except Exception:
        pass
