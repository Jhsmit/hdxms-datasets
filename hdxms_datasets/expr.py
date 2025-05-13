import narwhals as nw


PROTON_MASS = 1.0072764665789

# calculate centroid mass from charge and centroid M/Z
centroid_mass = (nw.col("charge") * (nw.col("centroid_mz") - PROTON_MASS)).alias("centroid_mass")

# calculate max uptake from seqeuence
max_uptake = nw.col("sequence").str.replace_all("P", "").str.len_chars().alias("max_uptake")


uptake = (nw.col("centroid_mass") - nw.col("nd_centroid_mass")).alias("uptake")
uptake_sd = ((nw.col("centroid_mass_sd") ** 2 + nw.col("nd_centroid_mass_sd") ** 2) ** 0.5).alias(
    "uptake_sd"
)

fd_uptake = (nw.col("fd_centroid_mass") - nw.col("nd_centroid_mass")).alias("fd_uptake")
fd_uptake_sd = (
    (nw.col("fd_centroid_mass_sd") ** 2 + nw.col("nd_centroid_mass_sd") ** 2) ** 0.5
).alias("fd_uptake_sd")

# relative fractional uptake; parial uptake / full uptake
f = nw.col("fd_uptake")
f_sd = nw.col("fd_uptake_sd")

p = nw.col("uptake")
p_sd = nw.col(["uptake_sd"])

rfu = (p / f).alias("rfu")
rfu_sd = (((p_sd**2 / f**2) + ((f_sd**2 * p**2) / f**4)) ** 0.5).alias("rfu_sd")
