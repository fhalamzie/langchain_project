try:
    import os
    import json
    import yaml
    import pandas as pd
    import fdb
    import numpy as np
    import re
    import random
    import hashlib
    from pathlib import Path
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.output_parsers import PydanticOutputParser
    from pydantic import BaseModel, Field
    import streamlit as st
    from faker import Faker
    
    print("Alle Module wurden erfolgreich importiert!")
except ImportError as e:
    print(f"Fehler beim Importieren: {e}")