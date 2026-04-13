from django.db import models


class Sabor(models.Model):
    nome = models.CharField(max_length=80)
    descricao = models.TextField()

    def __str__(self):
        nome = self.nome.upper()
        return f'({self.id}) {nome}'

    class Meta:
        verbose_name = 'Sabor'
        verbose_name_plural = 'Sabores'
