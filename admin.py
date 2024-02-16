# from flask import Blueprint, render_template
# from flask_login import login_required
# from mongo_setup import db
#
#
# admin = Blueprint('admin', __name__)
#
#
# @admin.route('/_admin')
# @login_required
# def admin_page():
#     collection = db['data']
#     first_document = collection.find_one()
#
#     if first_document and 'counter' in first_document:
#         n_gifts = first_document['counter']
#     else:
#         n_gifts = 0
#
#     return render_template('admin.html', n_gifts=n_gifts)
#
