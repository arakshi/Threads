import os

from app.core.config import get_settings


if __name__ == '__main__':
    s = get_settings()
    os.system(f'streamlit run app/ui/streamlit_app.py --server.port {s.ui_port}')
