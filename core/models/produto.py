from django.db import models


class Produto(models.Model):
    nome = models.CharField(max_length=80)
    descricao = models.CharField(max_length=255)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    imagem = models.ImageField(upload_to='produtos/')
    estoque = models.CharField(max_length=100)

    sabor = models.ForeignKey('Sabor', on_delete=models.PROTECT)
    categoria = models.ForeignKey('Categoria', on_delete=models.PROTECT)

    def __str__(self):
        nome = self.nome.upper()
        return f'({self.id}) {nome}'

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
