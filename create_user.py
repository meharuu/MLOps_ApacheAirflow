#!/usr/bin/env python3
"""
Create admin user for Airflow 2.7.3
"""

from airflow.www.security import AppBuilder
from airflow import settings
from flask_appbuilder.models.sqla import Base
from flask_appbuilder.security.sqla import User as FABUser

# Create session
session = settings.Session()

# Create user
user = FABUser()
user.username = 'admin'
user.email = 'admin@example.com'
user.firstname = 'Admin'
user.lastname = 'User'
user.set_password('admin')
user.is_active = True

# Get role
appbuilder = AppBuilder(settings.app)
role = appbuilder.sm.find_role("Admin")
user.roles = [role]

# Save
session.add(user)
session.commit()
session.close()

print("✅ Admin user created successfully!")
print("   Username: admin")
print("   Password: admin")