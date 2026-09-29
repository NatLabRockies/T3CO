# Installation

## Setting Up a Python Environment <a name="setting-up-a-python-environment"></a>

T3CO depends on [Python](https://www.python.org/downloads/)>=3.9. The default install supports Python up to 3.13. The FASTSim-integrated extras require Python>=3.9 and <=3.10. To create an environment containing the appropriate Python version and a built-in `pip`, there are two preferred ways:

1. First option is to use [**conda**](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html):

    if using Windows PowerShell, run an additional from Anaconda Prompt to enable conda capabilities:
    
    ```bash
    conda init powershell
    ```
    
    To create a python environment run,

    ```bash
    conda create -n t3co python=3.10
    conda activate t3co
    ```

    

2. The other option is using [venv](https://docs.python.org/3/library/venv.html)

    ```bash
    python3.10 -m venv t3co
    ```

    On macOS/Linux, activate the environment:

    ```bash
    source t3co/bin/activate
    ```

    On Windows Powershell:
    
    ```bash
    t3co\Scripts\activate
    ```

## Installing T3CO Python Package

T3CO is available on PyPI and as a public access GitHub repository. This gives the user **two sources** from where T3CO Python Package can be obtained and installed.

### Installation 'Extras'

The user can choose from these installation options or 'extras' of T3CO based on their desired tool capabilities. Extras can be combined, e.g. `t3co[viz,fastsim]`.

- T3CO as a pure cost estimation tool with exogenous inputs for energy terms (default version `t3co` - requires Python>=3.9, <=3.13)
- T3CO integrated with FASTSim for energy simulation (`t3co[fastsim]`, requires Python>=3.9,<=3.10)
- T3CO with plotting support for the [visualization module](./pages/visualization.md) — matplotlib, seaborn, and plotly (`t3co[viz]`, requires Python>=3.9,<=3.13)
- T3CO for developers and quality testers that includes all capabilities (`t3co[dev]` requires Python>=3.9,<=3.10)

The different 'extras' refers to different sets of dependencies that get installed along with T3CO when the user runs these commands. Dependencies don't need to be manually installed since [Poetry](https://python-poetry.org/) is used as the dependency manager.

To install a specific released version (for example T3CO v1.0.8):
```bash
pip install t3co==1.0.8
```

### Installation Source #1: From [PyPI](https://pypi.org/project/t3co/)

After creating a version-appropriate [Python environment](#setting-up-a-python-environment), the latest release of T3CO can be installed from PyPI using one of the following commands.

For the default option/extra:

```bash
pip install t3co
```

For the FASTSim-integrated 'extra':

```bash
pip install t3co[fastsim]
```

For the visualization 'extra' (enables `--plot` and the charts module):

```bash
pip install "t3co[viz]"
```

For the developer 'extra':

```bash
pip install t3co[dev]
```

### Installation Source #2: Cloning the [GitHub Repo](https://github.com/NatLabRockies/T3CO)

T3CO can also be installed from a clone of the GitHub repository.

First, [clone](https://git-scm.com/docs/git-clone) the repository from [GitHub](https://github.com/NatLabRockies/T3CO) from your desired directory (eg., /Users/Projects/):

```bash
git clone https://github.com/NatLabRockies/T3CO.git T3CO
```

This creates a git compliant folder 'T3CO' (i.e., a '/Users/Projects/T3CO' folder)

To access the `t3co-2.0` branch,

```bash
git checkout t3co-2.0
```

[GitHub Desktop](https://desktop.github.com/download/) is an application that provides a GUI for managing git clones. It gives the user a more interactive way of cloning a repo and switching branches. This option negates the need for`git clone` and a `git checkout` commands.

From within the [Python environment](#setting-up-a-python-environment), navigate to the parent directory containing the T3CO repository (run `cd T3CO`) and run one of these three installation options:

For the default option/extra:

```bash
pip install -e .
```

For the FASTSim-integrated 'extra':

```bash
pip install -e .[fastsim]
```

For the visualization 'extra':

```bash
pip install -e ".[viz]"
```

For the developer 'extra':

```bash
pip install -e .[dev]
```

### Post-Installation Checks

Check that the right version of T3CO is installed in your environment:

```bash
pip show t3co
```

If there are updates or new releases to T3CO that don't show in the local version when installing from a git clone, use a `git pull` command on the latest version from the `main` branch on the repo:

```bash
git pull origin main
```

Here 'main' can be replaced by the desired branch.


## Copying T3CO Demo Input Files <a name=copy-demo-inputs></a>

The `t3co.resources` module contains all the necessary input files needed for running T3CO. However, it is sometimes difficult to navigate to these files when installing. To help with this, run this command on the Command Line Interface.

```bash
install_t3co_demo_inputs
```

The user will receive these questions on the command line:

`Do you want to copy the T3CO demo input files? (y/n):`

`Enter the path where you want to copy demo input files:`

Choose `y` and provide the desired destination path to get a `demo_inputs` folder containing the `t3co.resources` module files copied to your local directory. To copy the folder to the current directory you are on, answer the second question with ".".

## Setting Up Environment Variables (Optional) <a name="env-setup"></a>

T3CO can fetch live fuel price projections from the EIA Annual Energy Outlook API when a US zipcode is provided in the Config `region` column. This feature requires a free API key.

**Step 1:** Register for a free API key at [eia.gov/opendata/register.php](https://www.eia.gov/opendata/register.php).

**Step 2:** Copy the example environment file to create your own `.env`:

```bash
cp .env.example .env
```

If you installed T3CO from PyPI (not a git clone), create a `.env` file manually in the directory where you run T3CO.

**Step 3:** Open `.env` and replace the placeholder with your actual API key:

```
T3CO_EIA_API_KEY=your_actual_api_key_here
```

If you are behind a corporate proxy with SSL inspection, you can also uncomment and set:

```
T3CO_SSL_VERIFY=false
```

The `.env` file is listed in `.gitignore` and will not be committed to version control. Never share your API key publicly.

If you don't set up a `.env` file, T3CO works normally using static fuel price data from `FuelPrices.csv`. The EIA integration is only activated when a zipcode is provided in the Config and the API key is available.

## Running your first analysis

To learn about the tool and run your first T3CO analysis, proceed to the [Quick Start Guide](./quick_start.md)