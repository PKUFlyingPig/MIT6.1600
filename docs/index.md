---
title: "6.1600 Lab Assignments"
---

[&larr; 6.1600 Home Page](https://61600.csail.mit.edu/)

## Lab assignments
{% for page in site.pages %}
{% if page.url contains "/lab" %}
* [{{ page.title }}]({{ page.url }})
{% endif %}
{% endfor %}  <!-- page -->
