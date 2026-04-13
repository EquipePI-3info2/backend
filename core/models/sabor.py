from django.db import models


class Sabor(models.Model):
    nome = models.CharField(max_length=80)
    descricao = models.CharField(max_length=255)

    def __str__(self):
        nome = self.nome.upper()
        return f'({self.id}) {nome}'
