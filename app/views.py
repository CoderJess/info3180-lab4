import os
from app import app, db, login_manager
from flask import render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from wtforms import FileField, SubmitField
from app.models import UserProfile
from app.forms import LoginForm
from app.forms import UploadForm


###
# Routing for application.
###

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html', name="Mary Jane")


@app.route('/upload', methods=['POST', 'GET'])
@login_required
def upload():
    # form class instantiation
    form = UploadForm()

    # Validate file upload on submit
    if form.validate_on_submit():
        # Get file data and save to the uploads folder
        file = form.file.data
        filename = secure_filename(file.filename)

        # Save the file to the upload folder
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        flash('File Saved', 'success')
        return redirect(url_for('upload'))

    return render_template('upload.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # Get the username and password values from the form.
        username = form.username.data
        password = form.password.data

        # Query the database for a user based on the username
        user = UserProfile.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            # Gets user id, load into session
            login_user(user)

            # Flash a message to the user
            flash('You have successfully logged in!', 'success')

            # Redirect the user to the upload form
            return redirect(url_for("upload"))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template("login.html", form=form)

@app.route('/uploads/<filename>')
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/files')
@login_required  # Ensure only logged-in users can access this route
def files():
    image_filenames = get_uploaded_images()  # Get the list of uploaded images
    return render_template('files.html', images=image_filenames)

@app.route('/logout')
@login_required  # Ensure only logged-in users can access this route
def logout():
    logout_user()  # Log out the user
    flash('You have been logged out successfully.', 'success')  # Flash message
    return redirect(url_for('home'))  # Redirect to the home route

# user_loader callback. This callback is used to reload the user object from
# the user ID stored in the session
@login_manager.user_loader
def load_user(id):
    return db.session.execute(db.select(UserProfile).filter_by(id=id)).scalar()

###
# The functions below should be applicable to all Flask apps.
###

# Flash errors from the form if validation fails
def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
), 'danger')
            
def get_uploaded_images():
    upload_folder = app.config['UPLOAD_FOLDER']
    images = []
    
    # Iterate over the contents of the uploads folder
    for subdir, dirs, files in os.walk(upload_folder):
        for file in files:
            images.append(file)
    return images

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404
