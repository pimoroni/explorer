export TERM=${TERM:="xterm-256color"}

MICROPYTHON_FLAVOUR="pimoroni"
MICROPYTHON_VERSION="b29530abbd0550c8ab6963024aef36f3cd6cd278"

PIMORONI_PICO_FLAVOUR="pimoroni"
PIMORONI_PICO_VERSION="37a1b6500f77924b2a3287009734bb24d4809bf1"

PIMORONI_PICOVECTOR_VERSION="020cf2317bdbde8f36a22aa2ea09b3af57ed29fb"

PY_DECL_VERSION="v0.0.5"
DIR2UF2_VERSION="v0.1.0"

BOARD="explorer_picovector"


function log_success {
	echo -e "$(tput setaf 2)$1$(tput sgr0)"
}

function log_inform {
	echo -e "$(tput setaf 6)$1$(tput sgr0)"
}

function log_warning {
	echo -e "$(tput setaf 1)$1$(tput sgr0)"
}

function ci_pimoroni_pico_clone {
    log_inform "Using Pimoroni Pico $PIMORONI_PICO_FLAVOUR/$PIMORONI_PICO_VERSION"
    git clone https://github.com/$PIMORONI_PICO_FLAVOUR/pimoroni-pico "$CI_BUILD_ROOT/pimoroni-pico"
    git -C "$CI_BUILD_ROOT/pimoroni-pico" checkout $PIMORONI_PICO_VERSION
    git -C "$CI_BUILD_ROOT/pimoroni-pico" submodule update --init
}

function ci_pimoroni_picovector_clone {
    log_inform "Using Pimoroni PicoVector pimoroni/$PIMORONI_PICOVECTOR_VERSION"
    git clone https://github.com/pimoroni/picovector-micropython "$CI_BUILD_ROOT/picovector-micropython"
    git -C "$CI_BUILD_ROOT/picovector-micropython" checkout $PIMORONI_PICOVECTOR_VERSION
    git -C "$CI_BUILD_ROOT/picovector-micropython" submodule update --init
}

function ci_micropython_clone {
    log_inform "Using MicroPython $MICROPYTHON_FLAVOUR/$MICROPYTHON_VERSION"
    git clone https://github.com/$MICROPYTHON_FLAVOUR/micropython "$CI_BUILD_ROOT/micropython"
    git -C "$CI_BUILD_ROOT/micropython" checkout $MICROPYTHON_VERSION
    git -C "$CI_BUILD_ROOT/micropython" submodule update --init lib/pico-sdk
    git -C "$CI_BUILD_ROOT/micropython" submodule update --init lib/cyw43-driver
    git -C "$CI_BUILD_ROOT/micropython" submodule update --init lib/lwip
    git -C "$CI_BUILD_ROOT/micropython" submodule update --init lib/mbedtls
    git -C "$CI_BUILD_ROOT/micropython" submodule update --init lib/micropython-lib
    git -C "$CI_BUILD_ROOT/micropython" submodule update --init lib/tinyusb
    git -C "$CI_BUILD_ROOT/micropython" submodule update --init lib/btstack
}

function ci_tools_clone {
    mkdir -p "$CI_BUILD_ROOT/tools"
    git clone https://github.com/gadgetoid/py_decl -b "$PY_DECL_VERSION" "$CI_BUILD_ROOT/tools/py_decl"
    git clone https://github.com/gadgetoid/dir2uf2 -b "$DIR2UF2_VERSION" "$CI_BUILD_ROOT/tools/dir2uf2"
}

function ci_micropython_build_mpy_cross {
    ccache --zero-stats || true
    CROSS_COMPILE="ccache " make -C "$CI_BUILD_ROOT/micropython/mpy-cross"
    ccache --show-stats || true
}

function ci_install_build_deps {
    sudo apt update && sudo apt install ccache
}

function ci_python_prepare {
    python3 -m pip install -r "${CI_BUILD_ROOT}/micropython/tools/mpremote/requirements.txt"
    python3 -m pip install littlefs-python==0.12.0
}

function ci_prepare_all {
    ci_tools_clone
    ci_micropython_clone
    ci_pimoroni_pico_clone
    ci_pimoroni_picovector_clone
    ci_micropython_build_mpy_cross
}

function ci_debug {
    log_inform "Project root: $CI_PROJECT_ROOT"
    log_inform "Build root: $CI_BUILD_ROOT"
}

function micropython_version {
    echo "MICROPY_GIT_TAG=$MICROPYTHON_VERSION, $BOARD $TAG_OR_SHA" >> $GITHUB_ENV
    echo "MICROPY_GIT_HASH=$MICROPYTHON_VERSION-$TAG_OR_SHA" >> $GITHUB_ENV
}

function ci_cmake_configure {
    TOOLS_DIR="$CI_BUILD_ROOT/tools"
    MICROPY_BOARD_DIR="$CI_PROJECT_ROOT/$BOARD"
    BUILD_DIR="$CI_BUILD_ROOT/build-$BOARD"
    cmake -S $CI_BUILD_ROOT/micropython/ports/rp2 -B "$BUILD_DIR" \
    -DPICOTOOL_FORCE_FETCH_FROM_GIT=1 \
    -DPICO_BUILD_DOCS=0 \
    -DPICO_NO_COPRO_DIS=1 \
    -DPICOTOOL_FETCH_FROM_GIT_PATH="$TOOLS_DIR/picotool" \
    -DPIMORONI_PICO_PATH="$CI_BUILD_ROOT/pimoroni-pico" \
    -DPICOVECTOR_MICROPYTHON_DIR="$CI_BUILD_ROOT/picovector-micropython" \
    -DPIMORONI_TOOLS_DIR="$TOOLS_DIR" \
    -DUSER_C_MODULES="$CI_PROJECT_ROOT/modules/picovector.cmake" \
    -DMICROPY_BOARD_DIR="$MICROPY_BOARD_DIR" \
    -DMICROPY_BOARD="$BOARD" \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
}

function ci_cmake_build {
    BUILD_DIR="$CI_BUILD_ROOT/build-$BOARD"
    ccache --zero-stats || true
    cmake --build $BUILD_DIR -j 2 || return $?
    ccache --show-stats || true

    if [ -z ${CI_RELEASE_FILENAME+x} ]; then
        CI_RELEASE_FILENAME=$BOARD
    fi

    log_inform "Copying -romfs.uf2 to $(pwd)/$CI_RELEASE_FILENAME.uf2"
    cp "$BUILD_DIR/firmware-romfs.uf2" $CI_RELEASE_FILENAME.uf2

    log_inform "Copying -romfs-with-filesystem.uf2 to $(pwd)/$CI_RELEASE_FILENAME-with-filesystem.uf2"
    cp "$BUILD_DIR/firmware-romfs-with-filesystem.uf2" $CI_RELEASE_FILENAME-with-filesystem.uf2
}

if [ -z ${CI_USE_ENV+x} ] || [ -z ${CI_PROJECT_ROOT+x} ] || [ -z ${CI_BUILD_ROOT+x} ]; then
    SCRIPT_PATH=${BASH_SOURCE-$0}
    SCRIPT_PATH=$(dirname "$SCRIPT_PATH")
    CI_PROJECT_ROOT=$(realpath "$SCRIPT_PATH/..")
    CI_BUILD_ROOT=$(pwd)
fi

ci_debug
