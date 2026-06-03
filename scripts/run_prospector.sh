#!/bin/bash
#
#SBATCH -p hsph # partition (queue)
#SBATCH --output=/n/holylabs/cgolden_lab/Lab/frontier/works/prospectors/prospectorGoogleDrive/logs/gd-prospector-%j.out
#SBATCH --error=/n/holylabs/cgolden_lab/Lab/frontier/works/prospectors/prospectorGoogleDrive/logs/gd-prospector-%j.err
#SBATCH -c 4 # number of cores 
#SBATCH --mem 5GB # memory 
#SBATCH -t 0-20:00 # time (D-HH:MM)
#SBATCH --mail-user=ttapera@hsph.harvard.edu
#SBATCH --mail-type=ALL

# Load environment (adjust to your setup)
source ~/.bashrc
cd /n/holylabs/cgolden_lab/Lab/frontier/works/prospectors/prospectorGoogleDrive

# Activate your environment
source .venv/bin/activate

echo "Running Google Drive Prospector..."

# Run the prospector
time google-drive-prospector dry_run=false

# save the logs
NOW=$( date '+%F_%H:%M:%S' )
git add logs
git commit -m "SCRONTAB ran at $NOW" 
