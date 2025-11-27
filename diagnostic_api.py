"""
Diagnostic script to check API setup
"""

import os
import sys
from pathlib import Path

def check_model_files():
    """Check if model files exist"""
    print("\n" + "="*80)
    print("1️⃣ CHECKING MODEL FILES")
    print("="*80)
    
    model_dir = Path('model')
    
    if not model_dir.exists():
        print("❌ Model directory doesn't exist: model/")
        return False
    
    required_files = [
        'trained_model.pkl',
        'preprocessor.pkl',
        'metadata.pkl'
    ]
    
    all_exist = True
    for file in required_files:
        file_path = model_dir / file
        if file_path.exists():
            size = file_path.stat().st_size / (1024*1024)  # Size in MB
            print(f"✅ {file} ({size:.2f} MB)")
        else:
            print(f"❌ {file} NOT FOUND")
            all_exist = False
    
    return all_exist


def check_src_structure():
    """Check if src structure is correct"""
    print("\n" + "="*80)
    print("2️⃣ CHECKING SRC STRUCTURE")
    print("="*80)
    
    required_files = [
        'src/__init__.py',
        'src/api/__init__.py',
        'src/api/main.py',
        'src/api/model_manager.py',
        'src/database/__init__.py',
        'src/database/config.py',
        'src/database/models.py'
    ]
    
    all_exist = True
    for file in required_files:
        file_path = Path(file)
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} NOT FOUND")
            all_exist = False
    
    return all_exist


def check_imports():
    """Check if imports work"""
    print("\n" + "="*80)
    print("3️⃣ CHECKING IMPORTS")
    print("="*80)
    
    try:
        sys.path.insert(0, os.getcwd())
        from src.database.config import test_connection
        print("✅ Can import database config")
    except Exception as e:
        print(f"❌ Cannot import database config: {e}")
        return False
    
    try:
        from src.api.model_manager import get_model_manager
        print("✅ Can import model manager")
    except Exception as e:
        print(f"❌ Cannot import model manager: {e}")
        return False
    
    try:
        from src.api.main import app
        print("✅ Can import FastAPI app")
    except Exception as e:
        print(f"❌ Cannot import FastAPI app: {e}")
        return False
    
    return True


def check_model_loading():
    """Try to load the model"""
    print("\n" + "="*80)
    print("4️⃣ CHECKING MODEL LOADING")
    print("="*80)
    
    try:
        import joblib
        
        model_path = Path('model/trained_model.pkl')
        if model_path.exists():
            model = joblib.load(model_path)
            print(f"✅ Model loaded successfully")
            print(f"   Type: {type(model)}")
        else:
            print(f"❌ Model file not found: {model_path}")
            return False
        
        preprocessor_path = Path('model/preprocessor.pkl')
        if preprocessor_path.exists():
            preprocessor = joblib.load(preprocessor_path)
            print(f"✅ Preprocessor loaded successfully")
            print(f"   Type: {type(preprocessor)}")
        else:
            print(f"❌ Preprocessor file not found: {preprocessor_path}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False


def check_database():
    """Check database connection"""
    print("\n" + "="*80)
    print("5️⃣ CHECKING DATABASE CONNECTION")
    print("="*80)
    
    try:
        sys.path.insert(0, os.getcwd())
        from src.database.config import test_connection
        
        if test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False


def check_environment():
    """Check environment variables"""
    print("\n" + "="*80)
    print("6️⃣ CHECKING ENVIRONMENT")
    print("="*80)
    
    from pathlib import Path
    from dotenv import load_dotenv
    import os as os_module
    
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file exists")
        load_dotenv()
        
        db_url = os_module.getenv('DATABASE_URL')
        if db_url:
            print(f"✅ DATABASE_URL set")
        else:
            print(f"❌ DATABASE_URL not set")
    else:
        print("❌ .env file not found")
        return False
    
    return True


def main():
    """Run all checks"""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "ML API DIAGNOSTIC CHECK".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    checks = [
        ("Environment", check_environment),
        ("Model Files", check_model_files),
        ("Src Structure", check_src_structure),
        ("Model Loading", check_model_loading),
        ("Database", check_database),
        ("Imports", check_imports),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n❌ Error in {check_name}: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    all_passed = True
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<30} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL CHECKS PASSED - API SHOULD WORK!")
        print("\nNow run:")
        print("  python3 run_api.py")
        print("Then test:")
        print("  python3 scripts/test_api.py")
    else:
        print("❌ SOME CHECKS FAILED - SEE ERRORS ABOVE")
        print("\nNext steps:")
        print("1. Check model files exist in model/")
        print("2. Train model if missing: python3 scripts/train_model.py")
        print("3. Check database connection in .env")
        print("4. Run: python3 scripts/init_database.py")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()