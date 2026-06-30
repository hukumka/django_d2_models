# D2 diagrams for django models


## Usage

1. Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # HERE! Order is unimportant, since it only adds management command.
    'django_d2_models',

    # user apps
    'apps.users',
    'apps.chat',
]
```

2. Run command to export models

```bash
python manage.py model_diagram > models.d2
```

3. Compile commands to `model.svg`

```bash
d2 models.d2
```

## Options

### exclude-apps

`--exclude-apps users --exclude-apps payment --exclude-apps feedback`

Exclude particular applications from rendering to declutter diagram

### user-apps-only

Exclude all third party applications from diagrams

### show-ref

Then set to true, show models referenced, even if they are from excluded apps.

Defaults to true

### abstract-models-depth

Show fields inherited from abstract model in separate model.
Value specifies how deep in inheritance tree this condition
will propagate.

Defaults to 1

To show always show fields from abstract models inline set to zero

```
--abstract-models-depth 0
```
