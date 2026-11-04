SCRIPT_PATH=${BASH_SOURCE-$0}
SCRIPT_PATH=$(dirname "$SCRIPT_PATH")
SCRIPT_PATH=$(realpath "$SCRIPT_PATH")

RUFF_VERSION="0.17.1"

function qa_prepare_all {
    pip install ruff==$RUFF_VERSION
}

function qa_check {
    ruff check --config "$SCRIPT_PATH/ruff.toml" "$@"
}

function qa_fix {
    ruff check --config "$SCRIPT_PATH/ruff.toml" --fix "$@"
}

function qa_examples_check {
    qa_check examples/
}

function qa_examples_fix {
    qa_fix examples/
}

function qa_modules_check {
    qa_check modules/py_frozen/
}

function qa_modules_fix {
    qa_fix modules/py_frozen/
}

function qa_picovector_check {
    qa_check modules/py_explorer/ filesystem/
}

function qa_picovector_fix {
    qa_fix modules/py_explorer/ filesystem/
}
