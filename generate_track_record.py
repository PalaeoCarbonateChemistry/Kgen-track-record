import numpy,json,subprocess,os,sys,requests,datetime,importlib
from matplotlib import pyplot

# Action should clone Kgen repository

def get_all_git_tags():
    # Returns a list of all git tags
    # Change to kgen directory
    os.chdir("./Kgen")
    # Get the tags
    tags = subprocess.check_output(['git', 'tag']).decode('ascii').strip().split("\n")
    # Change back to the original directory
    os.chdir("..")
    return tags

def get_gist_contents():
    # Returns the contents of a gist
    response = requests.get('https://gist.githubusercontent.com/rossidae/b93ca9f1a9e1702b4cfe3bf64a9be9d3/raw/0f31a4774ee7bb13e6a0c49e93c63747328178df/kgen_track_record.json')
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()

tags = get_all_git_tags()
existing_gist = get_gist_contents()

# Check if the tags are in the gist
untested_tags = [tag for tag in tags if tag not in existing_gist.keys()]
symbols = ["o","s","^","v","<",">","1","2","3","4"]

existing_gist["datetime"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
for tag in untested_tags:
    # Switch to Kgen directory
    os.chdir("./Kgen")

    # Checkout the tag
    output = subprocess.check_output(["git","checkout",tag])

    # Return to the original directory
    os.chdir("..")

    # Change pymyami version
    subprocess.check_output(["pip","uninstall","-y","pymyami"])
    subprocess.check_output(["pip","install","-r","./Kgen/python/requirements.txt"])

    # Import pymyami and kgen
    sys_modules = sys.modules.copy()
    for module in sys_modules:
        if "pymyami" in module or "kgen" in module:
            del sys.modules[module]

    pymyami = importlib.import_module("pymyami")
    kgen = importlib.import_module("kgen")

    # Palaeo seawater far from modern is the worst case scenario so we'll target that
    temperature = 40 # degrees C
    salinity = 30 # unitless (or psu if you like)
    pressure  = 5000/10 # bar (~depth/10)
    calcium = 40/1e3 # mol/kg ((mmol/kg)/1000)
    magnesium = 20/1e3 # mol/kg ((mmol/kg)/1000)

    # Do the calculation using Kgen
    Ks = kgen.calc_Ks(temp_c=temperature,sal=salinity,p_bar=pressure,magnesium=magnesium,calcium=calcium)
    existing_gist[tag] = Ks

# Save the results back to the JSON file
with open("./kgen_track_record.json","w") as file:
    file.write(json.dumps(existing_gist,indent=4))

# Extract the most recent three for comparison (or all of them if there aren't three commits yet)
relevant_tags = tags[-10:] if len(tags)>10 else tags

# Use the current one as the comparator
normaliser = existing_gist[tags[-1]]

# Iterate to quantify the difference as a percentage
K_differences = []
for tag in relevant_tags:
    current_K_difference = {}
    for K in normaliser.keys():
        current_K_difference[K] = ((existing_gist[tag][K]-normaliser[K])/normaliser[K])*100.0
    K_differences += [list(current_K_difference.values())]

# Generate a figure
figure,axes = pyplot.subplots(nrows=1)
axes = [axes]

k_names = ["K$_{0}^{*}$","K$_{1}^{*}$","K$_{2}^{*}$","K$_{W}^{*}$","K$_{B}^{*}$","K$_{S}^{*}$","K$_{spA}^{*}$","K$_{spC}^{*}$","K$_{P1}^{*}$","K$_{P2}^{*}$","K$_{P3}^{*}$","K$_{Si}^{*}$","K$_{F}^{*}$"]

for size,(K_difference,tag) in enumerate(zip(K_differences,relevant_tags,strict=True)):
    axes[0].plot(numpy.arange(0,len(normaliser)),K_difference,marker="o",label=tag,markersize=2*(6-size))


axes[0].set_xlim((0,len(normaliser)-1))
axes[0].set_xticks(numpy.arange(0,len(normaliser)))
axes[0].set_xticklabels(k_names)
axes[0].set_ylabel("Difference (%)")

pyplot.legend()

figure.savefig("./track_record.png")


