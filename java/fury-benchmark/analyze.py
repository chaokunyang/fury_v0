"""
    process fury/kryo/fst/hession performance data
"""
import datetime
import matplotlib.pyplot as plt
import os
import pandas as pd
import re

# dir_path = os.path.dirname(os.path.realpath(__file__))
import sys


def to_markdown(df: pd.DataFrame, filepath: str):
    with open(filepath + ".md", "w") as f:
        f.write(_to_markdown(df))


def _to_markdown(df: pd.DataFrame):
    lines = list(df.values.tolist())
    width = len(df.columns)
    lines.insert(0, df.columns.values.tolist())
    lines.insert(1, ["-------"] * width)
    md_table = "\n".join(
        ["| " + " | ".join([str(item) for item in line]) + " |" for line in lines]
    )
    return md_table


def process_data(filepath: str):
    df = pd.read_csv(filepath)
    columns = list(df.columns.values)
    for column in columns:
        if "Score Error" in column:
            df.drop([column], axis=1, inplace=True)
        if column == "Score":
            df.rename({"Score": "Tps"}, axis=1, inplace=True)
        if "Param: " in column:
            df.rename({column: column.replace("Param: ", "")}, axis=1, inplace=True)

    def process_df(bench_df):
        if bench_df.shape[0] > 0:
            benchmark_name = bench_df["Benchmark"].str.rsplit(
                pat=".", n=1, expand=True
            )[1]
            bench_df[["Lib", "Benchmark"]] = benchmark_name.str.rsplit(
                pat="_", n=1, expand=True
            )
            bench_df["Lib"] = bench_df["Lib"].str.capitalize()
            bench_df.drop(["Threads"], axis=1, inplace=True)
        return bench_df

    zero_copy_bench = df[df["Benchmark"].str.contains("ZeroCopy")]
    zero_copy_bench = process_df(zero_copy_bench)

    bench = df[~df["Benchmark"].str.contains("ZeroCopy")]
    bench = process_df(bench)

    return zero_copy_bench, bench


def plot(df: pd.DataFrame, file_dir, filename, column="Tps"):
    df["ns"] = 1 / df["Tps"] * 10**9
    data = df.fillna("")
    data.to_csv(f"{file_dir}/pd_{filename}")
    if "objectType" in data.columns:
        group_cols = ["Benchmark", "objectType", "bufferType"]
    else:
        group_cols = ["Benchmark", "bufferType"]
    grouped = data.groupby(group_cols)
    count = 0
    for keys, sub_df in grouped:
        count = count + 1
        sub_df = sub_df[["Lib", "references", column]]
        if keys[0].startswith("serialize"):
            title = " ".join(keys[:-1]) + " to " + keys[-1]
        else:
            title = " ".join(keys[:-1]) + " from " + keys[-1]
        title = "{} ({})".format(title, "Time" if column == "ns" else "Tps")
        save_filename = "{}_{:02d}_{}".format(
            filename, count, title.replace(" ", "_").replace("/", "")
        )
        fig, ax = plt.subplots()
        final_df = (
            sub_df.reset_index(drop=True)
            .set_index(["Lib", "references"])
            .unstack("Lib")
        )
        print(final_df)
        libs = final_df.columns.to_frame()["Lib"]
        color_map = {
            "Fury": "c",
            "Fury_deserialize": "c",
            # "Kryo": (1, 0.5, 1),
            # "Kryo": (1, 0.84, 0.25),
            "Kryo": (1, 0.65, 0.55),
            "Kryo_deserialize": (1, 0.65, 0.55),
            "Fst": (0.90, 0.43, 0.5),
            "Hession": (0.80, 0.5, 0.6),
            "Hession_deserialize": (0.80, 0.5, 0.6),
            "Protostuff": (1, 0.84, 0.66),
            "Jdk": (0.55, 0.40, 0.45),
            "Jsonb": (0.45, 0.40, 0.55),
        }
        color = [color_map[lib] for lib in libs]
        sub_plot = final_df.plot.bar(title=title, color=color, ax=ax, figsize=(7, 7))
        for container in ax.containers:
            ax.bar_label(container)
        ax.set_xlabel("enable_references")
        ax.set_ylabel(column)
        ax.legend(libs)
        save_dir = get_plot_dir(file_dir)
        sub_plot.get_figure().savefig(save_dir + "/" + save_filename)


def plot_zero_copy(df: pd.DataFrame, file_dir, filename, column="Tps"):
    df["ns"] = 1 / df["Tps"] * 10**9
    data = df.fillna("")
    data.to_csv(f"{file_dir}/pd_{filename}")
    if "dataType" in data.columns:
        group_cols = ["Benchmark", "dataType", "bufferType"]
    else:
        group_cols = ["Benchmark", "bufferType"]
    grouped = data.groupby(group_cols)
    count = 0
    for keys, sub_df in grouped:
        count = count + 1
        sub_df = sub_df[["Lib", "array_size", column]]
        if keys[0].startswith("serialize"):
            title = " ".join(keys[:-1]) + " to " + keys[-1]
        else:
            title = " ".join(keys[:-1]) + " from " + keys[-1]
        title = "{} ({})".format(title, "Time" if column == "ns" else "Tps")
        save_filename = "{}_{:02d}_{}".format(
            filename, count, title.replace(" ", "_").replace("/", "")
        )
        fig, ax = plt.subplots()
        final_df = (
            sub_df.reset_index(drop=True)
            .set_index(["Lib", "array_size"])
            .unstack("Lib")
        )
        print(final_df)
        libs = final_df.columns.to_frame()["Lib"]
        color_map = {
            "Fury": "c",
            "Kryo": (1, 0.65, 0.55),
            "Fst": (0.90, 0.43, 0.5),
            "Jsonb": (0.45, 0.40, 0.55),
        }
        color = [color_map[lib] for lib in libs]
        sub_plot = final_df.plot.bar(title=title, color=color, ax=ax, figsize=(7, 7))
        for container in ax.containers:
            ax.bar_label(container)
        ax.set_xlabel("array_size")
        ax.set_ylabel(column)
        ax.legend(libs)
        save_dir = get_plot_dir(file_dir)
        sub_plot.get_figure().savefig(save_dir + "/" + save_filename)


time_str = datetime.datetime.now().strftime("%m%d_%H%M_%S")


def get_plot_dir(_file_dir):
    plot_dir = _file_dir + "/" + time_str
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    return plot_dir


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z\\d])([A-Z])", r"\1_\2", name).lower()


def get_datasize_markdown(size_log):
    lines = [line.rsplit("===>", 1)[-1] for line in size_log.split("\n")]
    lines = [
        [item.strip() for item in line.split("|")][:-1] for line in lines if "|" in line
    ]
    columns = "Lib,objectType,references,bufferType,size".split(",")
    df = pd.DataFrame(lines, columns=columns)
    df["size"] = df["size"].astype(int)
    df = df["objectType,references,bufferType,size".split(",") + ["Lib"]]
    grouped_df = df.sort_values("objectType,references,bufferType,size".split(","))
    grouped_df = grouped_df[~grouped_df["bufferType"].str.contains("directBuffer")]
    grouped_df = grouped_df["objectType,references,Lib,size".split(",")]
    return _to_markdown(grouped_df)


if __name__ == "__main__":
    # size_markdown = get_datasize_markdown("""
    # """)
    # print(size_markdown)
    args = sys.argv[1:]
    if args:
        file_name = args[0]
    else:
        file_name = "jmh-result.csv"
    file_dir = "../.."
    zero_copy_bench, bench = process_data(os.path.join(file_dir, file_name))
    if zero_copy_bench.shape[0] > 0:
        to_markdown(
            zero_copy_bench, os.path.join(file_dir, f"{file_name}-zero_copy.md")
        )
        plot_zero_copy(zero_copy_bench, file_dir, "zero_copy_bench", column="ns")
    if bench.shape[0] > 0:
        to_markdown(bench, os.path.join(file_dir, f"{file_name}-bench.md"))
        plot(bench, file_dir, "bench", column="ns")
