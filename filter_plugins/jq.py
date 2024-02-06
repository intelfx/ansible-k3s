#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ivan Shapovalov <intelfx@intelfx.name>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

# language=yaml
DOCUMENTATION = '''
  name: jq
  short_description: run `jq` over input
  description:
    - This filter lets you pass the input through an arbitrary `jq` script.
    - If the `jq` script may produce multiple outputs, you must use O(_collect=True).
      Otherwise, multiple outputs are considered an error.
  positional: _input, expr
  options:
    _input:
      description:
        - The object to serialize to JSON and use as input to `jq`.
      type: any
      required: true
    expr:
      description:
        - The `jq` expression to evaluate.
        - See U(https://jqlang.github.io/jq/) for documentation and examples.
      type: string
      required: true
    _collect:
      description:
        - Whether to collect multiple outputs into an array.
        - If omitted or False, multiple outputs are considered an error.
      type: bool
      required: false
      default: false
    kwargs...:
      description:
        - Any keyword arguments will be JSON-encoded and passed to `jq` as named variables.
      type: any
      required: false
  requirements:
    - jq
'''

# language=yaml
EXAMPLES = '''
- name: Define data to work on in the examples below
  ansible.builtin.set_fact:
    domain_definition:
      domain:
        cluster:
          - name: cluster1
          - name: cluster2
        server:
          - name: server11
            cluster: cluster1
            port: '8080'
          - name: server12
            cluster: cluster1
            port: '8090'
          - name: server21
            cluster: cluster2
            port: '9080'
          - name: server22
            cluster: cluster2
            port: '9090'
          - name: server31
            cluster: cluster3
            port: '10010'
          - name: server32
            cluster: cluster3
            port: '10020'
        library:
          - name: lib1
            target: cluster1
          - name: lib2
            target: cluster2

- name: Display all cluster names
  ansible.builtin.debug:
    var: item
  loop: "{{ domain_definition | jq('.domain.cluster | map(.name)') }}"

- name: Display all server names
  ansible.builtin.debug:
    var: item
  loop: "{{ domain_definition | jq('.domain.server | map(.name)') }}"

- name: Display all ports from cluster1
  ansible.builtin.debug:
    var: item
  loop: "{{ domain_definition | jq(query) }}"
  vars:
    query: '.domain.server | map(select(.cluster == "cluster1")) | map(.port)'

- name: Display all ports from cluster1 as a string
  ansible.builtin.debug:
    msg: "{{ domain_definition | jq(query) | join(', ') }}"
  vars:
    query: '.domain.server | map(select(.cluster == "cluster1")) | map(.port)'

- name: Display all server ports and names from cluster2
  ansible.builtin.debug:
    var: item
  loop: "{{ domain_definition | jq(query) }}"
  vars:
    query: '.domain.server | map(select(.cluster == "cluster2")) | map({ port, name })'

- name: Display all ports from servers whose name starts with "server1"
  ansible.builtin.debug:
    msg: "{{ domain_definition | jq(query) }}"
  vars:
    query: '.domain.server | map(select(.name | startswith("server1"))) | map(.port)'

- name: 'Advanced: display names of all servers in clusters from the "clusters" array'
  ansible.builtin.debug:
    msg: "{{ {} | jq(query, clusters=domain_definition.domain.cluster, servers=domain_definition.domain.server) }}"
  vars:
    query: '$clusters | map(. as $c | $servers | map(. as $s | select($s.cluster == $c.name)) | .[]) | map(.name)'
'''

# language=yaml
RETURN = '''
  _value:
    description:
      - The output of `jq`, deserialized from JSON.
    type: any
'''

import json
import re
import subprocess
from ansible.errors import AnsibleFilterError
from ansible.parsing.ajson import AnsibleJSONEncoder
from typing import (
    Any,
    Generator,
)


def json_loads_multiple(data: str, **kwargs) -> Generator[Any, None, None]:
    decoder = json.JSONDecoder(**kwargs)
    pattern = re.compile(r'\S', re.ASCII)
    pos, end = 0, len(data) + 1
    while pos < end:
        obj, pos = decoder.raw_decode(data, pos)
        yield obj
        m = pattern.search(data, pos)
        pos = m.start() if m is not None else end


def jq(data, expr, **kwargs):
    collect = kwargs.pop('_collect', False)

    input_text = json.dumps(data, cls=AnsibleJSONEncoder, preprocess_unsafe=False)
    kwargs_text = {
        str(k): json.dumps(v, cls=AnsibleJSONEncoder, preprocess_unsafe=False)
        for k, v
        in kwargs.items()
    }
    expr_text = str(expr)

    jq_cmdline = [
        'jq',
        '--ascii-output',
    ] + [
        arg
        for k, v in kwargs_text.items()
        for arg in [ '--argjson', k, v ]
    ] + [
        '--',
        expr_text,
    ]

    try:
        result = subprocess.run(
            jq_cmdline,
            input=input_text,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        if e.stderr and e.returncode != 0:
            raise AnsibleFilterError(f'jq error (rc={e.returncode}): {e.stderr}')

        raise AnsibleFilterError(f'jq invocation error: {e}')

    if result.stderr:
        raise AnsibleFilterError(f'jq produced non-empty stderr: {result.stderr}')

    output_text = result.stdout

    try:
        if collect:
            output = list(json_loads_multiple(output_text))
        else:
            output = json.loads(output_text)
    except json.JSONDecodeError as e:
        raise AnsibleFilterError(f'jq output is not a valid JSON: {e}')

    return output


class FilterModule(object):
    def filters(self):
        return {
            'jq': jq,
        }
