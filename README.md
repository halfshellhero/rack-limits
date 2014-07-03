rack-limits
===========

API Limits scripts

Description
===========

limits_per_region_us.py will gather usage and currently set limits in all regions available to US accounts for the following:

* Compute Ram
* Compute Instance
* Private Networks
* Cloud Load Balancers (LBaaS)
* CBS Ram
* CBS Volume

limits_per_region.py can be used for any account (US or UK) and will return the same usage and limits as the US script, but only currently works on a single region at a time.

Usage
=====

python limits_per_region_us.py -u $USERNAME -a $ACCOUNT

python limits_per_region.py -r $REGION -u $USERNAME -a $ACCOUNT
