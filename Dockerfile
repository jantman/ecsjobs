FROM <FROM IMAGE>

# for labeling image at build time
ARG git_commit
ARG git_url
ARG build_time


# apply the labels
LABEL git_commit=$git_commit git_url=$git_url build_time=$build_time
