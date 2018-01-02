PMOD="service-utilities"
PMOD_="service_utilities"
VENV="venv"
PROJECT_BASE="/research_data/code/git/"
PROJECT=$PROJECT_BASE/$PMOD/

VIRTUAL_ENV=$PROJECT/$VENV
PYTHON=$VIRTUAL_ENV"/bin/python3"
# cleanup local directory

rm -r $VIRTUAL_ENV/lib/python3.5/site-packages/$PMOD_* \
    $PROJECT/$PMOD_.egg-info/ \
    $PROJECT/dist/ \
    $PROJECT/build/ \
    $PROJECT/src/$PMOD_.egg-info/

$PYTHON setup.py install

