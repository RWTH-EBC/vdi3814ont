from pathlib import Path
import owlrl
import rdflib
from rdflib import Graph
from pyshacl import validate


def filter_by_namespace(g, ns_to_keep: rdflib.Namespace) -> Graph:
    filtered_graph = Graph()

    for s, p, o in g:
        if (str(s).startswith(str(ns_to_keep)) or
                str(p).startswith(str(ns_to_keep)) or
                str(o).startswith(str(ns_to_keep))):
            filtered_graph.add((s, p, o))

    return filtered_graph


def load_graph(path: Path) -> Graph:
    g = Graph()
    g.parse(path.as_posix(), format="turtle")
    return g


def validate_with_pyshacl(shacl_graph, data_graph):
    return validate(
        data_graph=data_graph,
        shacl_graph=shacl_graph,
        ont_graph=None,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        debug=False,
    )


def reason_with_owlrl(graph: Graph, new_graph: bool = False) -> Graph:
    """
    Performs OWLRL reasoning on a graph.

    Args:
        graph: The input RDF graph.
        new_graph: If True, returns a new graph with the reasoned triples.
                   If False, modifies the original graph in place.

    Returns:
        The graph with inferred triples.
    """

    if new_graph:
        # Create a new graph and copy the original triples into it.
        reasoned_graph = rdflib.Graph()
        reasoned_graph += graph
    else:
        reasoned_graph = graph

    # Perform the reasoning, which modifies the graph in-place.
    owlrl.DeductiveClosure(
        owlrl.OWLRL_Semantics,
        axiomatic_triples=True,
        datatype_axioms=True,
    ).expand(reasoned_graph)

    return reasoned_graph


if __name__ == "__main__":

    # load the ontology graph and data graph
    shacl_graph = Graph().parse("graphs/vdi3814.ttl", format="turtle")
    data_graph = Graph().parse("graphs/instance.ttl", format="turtle")

    # reason the data graph with OWL RL
    reasoned = reason_with_owlrl(shacl_graph + data_graph)
    reasoned = filter_by_namespace(reasoned, rdflib.Namespace("http://www.vdi.de/3814#"))

    # validate the reasoned graph against the SHACL shapes
    confirms, results_graph, results_text = validate_with_pyshacl(shacl_graph, reasoned)

    # save the validation report
    results_graph.serialize(destination="graphs/validation_report.ttl", format="turtle")

    # print the validation results
    print(results_text)
